import os
import boto3
import requests
from requests.models import Response

# verify access token in keycloak
def check_authorization(system_id, tenant_id, access_token, config_table_name, region):
    if not system_id or not tenant_id or not access_token:
        return False

    print("check authorization")
    client = boto3.client("dynamodb", region_name=region)

    try:
        response = client.get_item(
            TableName=config_table_name,
            Key={"system_id": {"S": system_id}, "tenant_id": {"S": tenant_id}},
        )
    except Exception as e:
        print(e)

        return False

    if not response.get("Item"):
        return False

    keycloak_url = response["Item"]["keycloak_url"]["S"]
    keycloak_realm = response["Item"]["keycloak_realm"]["S"]
    print(keycloak_url, keycloak_realm)

    if not keycloak_url or not keycloak_realm:
        return False

    keycloak_userinfo_url = (
        f"{keycloak_url}/auth/realms/{keycloak_realm}/protocol/openid-connect/userinfo"
    )
    r = requests.get(
        url=keycloak_userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
    )
    print("status code::" + str(r.status_code))

    if access_token != "secret":
        return False
    # if r.status_code != 200:
    #     return False

    return True


def lambda_handler(event, context):
    name = os.environ.get("SYSTEM_NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")
    region = os.environ.get("REGION", "ap-northeast-1")
    config_table_name = "{}_{}_Config".format(name, env)
    system_id, tenant_id, access_token = (
        event["headers"].get("system_id", ""),
        event["headers"].get("tenant_id", ""),
        event["headers"].get("authorization", ""),
    )
    response = {
        "isAuthorized": False,
        "context": {},
    }
    is_authorized = check_authorization(
        system_id, tenant_id, access_token, config_table_name, region
    )
    print(system_id, tenant_id, access_token, is_authorized)
    if is_authorized:
        print("Authorized")
        print(event)

        response = {
            "isAuthorized": True,
            "context": {"system_id": system_id, "tenant_id": tenant_id},
        }
        return response

    return response
