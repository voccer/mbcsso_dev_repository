import os
import json
import boto3

import requests
import ast
import base64

from aws_xray_sdk.core import xray_recorder

timeout = 10


@xray_recorder.capture("put password")
def setup_password(user_id, password, admin, token):
    print(f"start setup password with user_id: {user_id}, password: {password}")
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}/reset-password"
    print(f"setup password url: {url}")

    print(f"setup password token: {token}")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    ## decrypt password by kms
    kms_client = boto3.client("kms")
    kms_key_id = os.environ.get("KMS_KEY_ID")
    password = kms_client.decrypt(
        KeyId=kms_key_id, CiphertextBlob=bytes(base64.b64decode(password))
    )
    print(f"set up decrypted password::{password}")

    payload = {"type": "password", "value": password, "temporary": False}
    response = requests.request(
        "PUT", url=url, headers=headers, json=payload, verify=False, timeout=timeout
    )

    print(f"set up password::{response.status_code}")


@xray_recorder.capture("get user_id keycloak")
def get_user_id(username, admin, token):
    print(f"start get user_id with username: {username}")

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users?username={username}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = requests.request("GET", url=url, headers=headers, timeout=timeout).json()
    if len(response) == 0:
        return None

    for resp in response:
        if str(resp["username"]).strip() == str(username).strip():
            return resp["id"]
    return None


@xray_recorder.capture("get group_id keycloak")
def get_group_id(group_name, admin, token):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = (
        f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/groups?search={group_name}"
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = requests.request("GET", url=url, headers=headers, timeout=timeout).json()
    print(f"get group_id with::{response}")
    if len(response) == 0:
        return None

    for resp in response:
        if str(resp["name"]).strip() == str(group_name).strip():
            return resp["id"]
    return None


@xray_recorder.capture("get token admin account")
def get_token(admin):
    print(f"start get token with admin: {admin}")

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/realms/{keycloak_realm}/protocol/openid-connect/token"
    client_id = admin["client_id"]
    username = admin["admin"]
    password = admin["password"]

    #  get plaintext password from kms
    system_name = os.environ.get("SYSTEM_NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")
    alias = f"alias/{system_name}_{env}_key_{username}"

    kms_client = boto3.client("kms")
    decrypted_password = kms_client.decrypt(
        KeyId=alias, CiphertextBlob=bytes(base64.b64decode(password))
    )
    decrypted_password = decrypted_password["Plaintext"].decode("utf-8")
    print(f"plaintext password: {decrypted_password}")

    params = {
        "client_id": client_id,
        "username": username,
        "password": decrypted_password,
        "grant_type": "password",
    }

    return ast.literal_eval(
        requests.post(url, params, verify=False).content.decode("utf-8")
    )["access_token"]


@xray_recorder.capture("sync:: create user")
def create_user(data, admin):
    print(f"sync:: create user with data: {data}")
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users"
    username = data["id"]["S"].split("#")[-1]
    payload = {
        "enabled": True,
        "groups": [],
        "emailVerified": "",
        "username": username,
    }

    token = get_token(admin)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    if "first_name" in data:
        payload["firstName"] = data["first_name"]["S"]
    if "last_name" in data:
        payload["lastName"] = data["last_name"]["S"]
    if "attributes" in data:
        payload["attributes"] = {}
        for att in data["attributes"]["M"]:
            payload["attributes"][att] = [data["attributes"]["M"][att]["S"]]

    print(f"sync create user payload:: {payload}")
    code = requests.request(
        "POST", url=url, headers=headers, json=payload, verify=False
    ).status_code

    print("sync:: create user with code: ", code)
    if str(code) == "201":
        if "password" in data:
            password = data["password"]["S"]
            user_id = get_user_id(username, admin, token)
            if not user_id:
                print("warning: user not found when set password")

                return
            setup_password(user_id, password, admin, token)


@xray_recorder.capture("sync:: delete user")
def delete_user(data, admin):
    username = data["id"]["S"]
    username = str(username).strip().split("#")[-1]

    token = get_token(admin)

    user_id = get_user_id(username, admin, token)
    if not user_id:
        print(f"user not found when delete user::{username}")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}"

    requests.request("DELETE", url=url, headers=headers)


@xray_recorder.capture("sync:: update user")
def update_user(data, admin):
    username = data["id"]["S"].strip().split("#")[-1]

    token = get_token(admin)

    user_id = get_user_id(username, admin, token)
    if not user_id:
        print(f"user not found when update user::{username}")
        return

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {"username": username}

    if "last_name" in data:
        payload["lastName"] = data["last_name"]["S"]
    if "first_name" in data:
        payload["firstName"] = data["first_name"]["S"]
    if "email" in data:
        payload["email"] = data["email"]["S"]

    if "password" in data:
        password = data["password"]["S"]
        setup_password(user_id, password, admin, token)

    return requests.request(
        "PUT", url=url, headers=headers, json=payload, verify=False
    ).status_code


@xray_recorder.capture("sync:: create group")
def create_group(data, admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/groups"
    token = get_token(admin)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {"name": data["id"]["S"].strip().split("#")[-1]}

    return requests.request(
        "POST", url, json=payload, headers=headers, verify=False
    ).status_code


@xray_recorder.capture("sync:: delete group")
def delete_group(data, admin):
    group_name = data["id"]["S"]
    group_name = str(group_name).strip().split("#")[-1]

    token = get_token(admin)

    group_id = get_group_id(group_name, admin, token)

    if not group_id:
        print("group not found")

        return

    print(group_name, group_id)

    headers = {
        "authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "cache-control": "no-cache",
    }
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = (
        f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/groups/"
        + str(group_id).strip()
    )

    return requests.delete(url=url, headers=headers).status_code


@xray_recorder.capture("sync:: add member group")
def create_member_group(data, admin):
    group_name = str(data["id"]["S"]).strip().split("#")[-1]
    user_name = str(data["sk"]["S"]).strip().split("#")[-1]

    token = get_token(admin)

    user_id = get_user_id(user_name, admin, token)
    group_id = get_group_id(group_name, admin, token)

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}/groups/{group_id}"

    if not user_id or not group_id:
        print("user or group not found")

        return

    headers = {
        "authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "cache-control": "no-cache",
    }
    payload = {"realms": keycloak_realm, "userID": user_id, "groupID": group_id}
    print(f"url:: {url}, payload:: {payload}")

    return requests.request("PUT", url=url, headers=headers, json=payload).status_code


@xray_recorder.capture("sync:: delete member group")
def delete_member_group(data, admin):
    group_name = str(data["id"]["S"]).strip().split("#")[-1]
    user_name = str(data["sk"]["S"]).strip().split("#")[-1]

    token = get_token(admin)

    user_id = get_user_id(user_name, admin, token)
    group_id = get_group_id(group_name, admin, token)

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}/groups/{group_id}"
    print(f"sync:: delete member group url:: {url}")

    if not user_id or not group_id:
        print("user or group not found")

        return

    headers = {
        "authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "cache-control": "no-cache",
    }
    return requests.request("DELETE", url=url, headers=headers).status_code


## ----------update to db---------------- ##


@xray_recorder.capture("push db:: create data")
def create_data(table_name, data):
    print(f"create_data: {table_name}")
    print(f"create_data: {data}")

    data_without_password = data.copy()

    if "password" in data_without_password:
        del data_without_password["password"]

    client = boto3.client("dynamodb")
    client.put_item(TableName=table_name, Item=data_without_password)


@xray_recorder.capture("push db:: delete data")
def delete_data(table_name, data):
    print(f"delete_data: {table_name}")
    print(f"delete_data: {data}")
    client = boto3.client("dynamodb")
    client.delete_item(TableName=table_name, Key=data)


@xray_recorder.capture("sync and put data to db")
def lambda_handler(event, context):
    print(f"process sqs event: {event}")
    system_name = os.environ.get("SYSTEM_NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")
    region = os.environ.get("REGION", "ap-northeast-1")

    config_table_name = f"{system_name}_{env}_Config"
    config_table = boto3.resource("dynamodb", region_name=region).Table(
        config_table_name
    )

    for record in event["Records"]:
        body = json.loads(record["body"])

        message = json.loads(body["Message"])
        sso_type = message.get("sso_type")
        # if sso_type != "keycloak":
        #     continue

        for mess in message["infos"]:
            system_id, tenant_id = mess["system_id"], mess["tenant_id"]
            users_table_name = f"{system_name}_{env}_{system_id}_{tenant_id}_users"

            data = mess["data"]
            event_name = mess["event_name"]

            sk = data["sk"]["S"]
            pk = data["id"]["S"].split("#")[0]

            if sk.startswith("config#"):
                continue

            admin_item = config_table.get_item(
                Key={"system_id": system_id, "tenant_id": tenant_id}
            )

            admin = admin_item.get("Item")
            print(f"admin: {admin}")

            command = data.get("command", {}).get("S")

            print(f"command: {command}")
            if event_name == "INSERT" or event_name == "MODIFY":
                # save to db
                create_data(users_table_name, data)

                # sync to keycloak
                if command == "add":
                    if sk == "config":
                        if pk == "user":
                            create_user(data, admin)
                        else:
                            create_group(data, admin)
                elif command == "update":
                    if sk == "config" and pk == "user":
                        update_user(data, admin)
                elif command == "delete":
                    if sk == "config":
                        if pk == "user":
                            delete_user(data, admin)
                        else:
                            delete_group(data, admin)
                elif sk.startswith("member#"):
                    print(f"sync create member_group")
                    resp = create_member_group(data, admin)
                    print(f"create member:: {resp}")

            elif event_name == "REMOVE" and sk.startswith("member#"):
                print(f"delete member group")
                delete_data(users_table_name, data)
                print(f"sync:: delete member_group")
                delete_member_group(data, admin)
            else:
                print("event exception")
            # sysn to keycloak

            # if command == "add":
            #     if sk == "config":
            #         if pk == "user":
            #             create_user(data, admin)
            #         else:
            #             create_group(data, admin)
            #     elif sk == "member":
            #         create_member_group(data, admin)
            # elif command == "update":
            #     if sk == "config":
            #         if pk == "user":
            #             update_user(data, admin)

            # elif command == "delete":
            #     if sk == "config":
            #         if pk == "user":
            #             delete_user(data, admin)
            #         else:
            #             delete_group(data, admin)
            #     elif sk == "member":
            #         delete_member_group(data, admin)

    # TODO: sync data to keycloak
    # print("sync data to keycloak")
    # for record in event["Records"]:
    #     body = json.loads(record["body"])

    #     message = json.loads(body["Message"])
    #     sso_type = message.get("sso_type", "")
    #     if sso_type != "keycloak":
    #         continue

    #     for mess in message["infos"]:
    #         system_id, tenant_id = mess["system_id"], mess["tenant_id"]
    #         data = mess["data"]
    #         region = os.environ.get("REGION", "ap-northeast-1")
    #         table_name = f"{system_name}_{env}_Config"

    #         table = boto3.resource("dynamodb", region_name=region).Table(table_name)
    #         resp = table.get_item(Key={"system_id": system_id, "tenant_id": tenant_id})

    #         admin = resp.get("Item")

    #         print(f"admin: {admin}")

    #         sk = str(data["sk"]["S"]).strip()
    #         pk = str(data["id"]["S"]).strip().split("#")[0]
    #         if sk.startswith("config#"):
    #             continue

    #         if event_name == "INSERT":
    #             if sk == "config":
    #                 if pk == "user":
    #                     create_user(data, admin)
    #                 else:
    #                     create_group(data, admin)
    #             if sk == "member":
    #                 create_member_group(data, admin)
    #         elif event_name == "MODIFY":
    #             if sk == "config":
    #                 if pk == "user":
    #                     update_user(data, admin)
    #         elif event_name == "REMOVE":
    #             if sk == "config":
    #                 if pk == "user":
    #                     delete_user(data, admin)
    #                 else:
    #                     delete_group(data, admin)
    #             if sk == "member":
    #                 delete_member_group(data, admin)

    # TODO: push to eventbridge

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
