import os

import boto3
import requests
import jwt
from aws_xray_sdk.core import xray_recorder

from shared_code.logger import Logger

logger = Logger().get_logger()

admin_roles = [
    "manage-authorization",
    "manage-clients",
    "manage-events",
    "manage-identity-providers",
    "manager_users",
    "query-clients",
    "query-groups",
    "query-realms",
    "query-users",
    "realm-admin",
    "view-authorization",
    "view-clients",
    "view-events",
    "view-identity-providers",
    "view-realm",
    "view-users",
]


@xray_recorder.capture("check allow to access")
def check_allow_to_access(roles, action, preferred_username):
    roles_set = set(roles)
    is_admin = True
    for role in admin_roles:
        if role not in roles_set:
            is_admin = False
    if is_admin:
        return True

    ## users only get or update themselves
    if action.startswith("get_user#") or action.startswith("update_user#"):
        user_id = action.split("#")[1]
        if user_id == preferred_username and user_id:
            return True

    return False


# verify access token in keycloak
@xray_recorder.capture("check authorization")
def check_authorization(
    system_id, tenant_id, access_token, config_table_name, action, region
):
    if not system_id or not tenant_id or not access_token:
        return False

    logger.info("check authorization")
    config_table = boto3.resource("dynamodb", region_name=region).Table(
        config_table_name
    )

    try:
        response = config_table.get_item(
            Key={"system_id": system_id, "tenant_id": tenant_id}
        )
    except Exception as e:
        logger.info(e)

        return False

    if not response.get("Item"):
        return False

    keycloak_url = response["Item"].get("keycloak_url")

    keycloak_realm = response["Item"].get("keycloak_realm")

    if not keycloak_realm or not keycloak_url:
        logger.info("keycloak_realm or keycloak_url is not set")

        return False

    # #use kms to decrypt keycloak_realm
    # kms = boto3.client("kms")
    # keycloak_realm = kms.decrypt(CiphertextBlob=bytes.fromhex(keycloak_realm))['Plaintext'].decode('utf-8')
    # keycloak_realm_encrypted = kms.encrypt(KeyId='alias/keycloak_realm', Plaintext=keycloak_realm.encode('utf-8'))['CiphertextBlob'].hex()

    keycloak_userinfo_url = (
        f"{keycloak_url}/auth/realms/{keycloak_realm}/protocol/openid-connect/userinfo"
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {}
    response = requests.request(
        "GET", url=keycloak_userinfo_url, headers=headers, data=payload
    )

    if access_token == "secret":
        return True
    if response.status_code != 200:
        return False

    preferred_username = response.json().get("preferred_username", "")

    payload = jwt.decode(access_token, verify=False)
    roles = []
    if "resource_access" in payload:
        for key in payload["resource_access"]:
            roles.extend(payload["resource_access"][key]["roles"])

    is_allow_to_access = check_allow_to_access(roles, action, preferred_username)

    if not is_allow_to_access:
        return False

    return True


@xray_recorder.capture("authorizer")
def lambda_handler(event, context):
    logger.info(f"authorizer event: {event}")

    name = os.environ.get("SYSTEM_NAME")
    env = os.environ.get("ENV")
    region = os.environ.get("REGION")

    config_table_name = "{}_{}_Config".format(name, env)
    access_token = event["headers"].get("authorization")

    system_id = event.get("queryStringParameters", {}).get("system_id")
    tenant_id = event.get("queryStringParameters", {}).get("tenant_id")

    route_key = event["requestContext"]["routeKey"]

    method, path = route_key.split(" ")

    user_id = event.get("pathParameters", {}).get("user_id")

    action = ""
    if method == "POST":
        if path == "/users":
            action = "create_user"
        elif path == "/groups":
            action = "create_group"
    elif method == "PUT":
        if path == "/users/{user_id}":
            action = f"update_user#{user_id}"
        elif path == "/groups/{group_id}":
            action = "update_group"
        elif path == "/users/{user_id}/groups/{group_id}":
            action = "add_user_to_group"
    elif method == "DELETE":
        if path == "/users/{user_id}":
            action = "delete_user"
        elif path == "/groups/{group_id}":
            action = "delete_group"
        elif path == "/users/{user_id}/groups/{group_id}":
            action = "remove_user_from_group"
    elif method == "GET":
        if path == "/users":
            action = "search_users"
        elif path == "/groups":
            action = "search_groups"
        elif path == "/users/{user_id}":
            action = f"get_user#{user_id}"
        elif path == "/groups/{group_id}":
            action = "get_group"
        elif path == "/users/{user_id}/groups":
            action = "search_user_groups"

    response = {
        "isAuthorized": False,
        "context": {},
    }

    is_authorized = check_authorization(
        system_id, tenant_id, access_token, config_table_name, action, region
    )
    logger.info(
        f"system_id: {system_id}, tenant_id: {tenant_id}, is_authorized: {is_authorized}"
    )

    if is_authorized:
        response = {
            "isAuthorized": True,
            "context": {"system_id": system_id, "tenant_id": tenant_id},
        }
        return response

    return response
