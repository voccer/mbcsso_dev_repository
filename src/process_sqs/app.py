import os
import json
import boto3

import requests
import ast


def set_up_password(user_id, password, admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}/reset-password"
    token = get_token(admin)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }
    payload = {"type": "password", "value": password, "temporary": False}

    return requests.request(
        "PUT", url=url, headers=headers, json=payload, verify=False
    ).status_code


def get_user_id(username, admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/?username=" + str(
        username
    )

    token = get_token()

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }

    return requests.get(url=url, headers=headers).json()[0]["id"]


def get_group_id(group_name, admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}dev/groups?search=" + str(
        group_name
    )

    token = get_token(admin)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }

    return requests.get(url=url, headers=headers).json()[0]["id"]


def get_token(admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/realms/{keycloak_realm}/protocol/openid-connect/token"
    client_id = admin["client_id"]
    username = admin["admin"]
    password = admin["password"]

    params = {
        "client_id": client_id,
        "username": username,
        "password": password,
        "grant_type": "password",
    }

    return ast.literal_eval(
        requests.post(url, params, verify=False).content.decode("utf-8")
    )["access_token"]


def create_user(data, admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users"
    username = data.get("id").strip().split("#")[-1]
    payload = {
        "enabled": True,
        "attributes": {},
        "groups": [],
        "emailVerified": "",
        "username": username,
    }

    token = get_token(admin)
    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }

    if "first_name" in data:
        payload["firstName"] = data["first_name"]
    if "last_name" in data:
        payload["lastName"] = data["last_name"]

    code = requests.post(
        url=url, headers=headers, json=payload, verify=False
    ).status_code
    if str(code) == "201":
        if "password" in data:
            password = data["password"]
            user_id = get_user_id(username, admin)

            set_up_password(user_id, password, admin)


def delete_user(data, admin):
    username = data["id"]
    username = str(username).strip().split("#")[-1]

    user_id = get_user_id(username, admin)

    token = get_token(admin)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = (
        f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/"
        + str(user_id).strip()
    )

    requests.delete(url=url, headers=headers)


def update_user(data, admin):
    username = data.get("id").strip().split("#")[-1]

    user_id = get_user_id(username, admin)

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}"

    token = get_token(admin)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }
    payload = {"username": username}

    if "last_name" in data:
        payload["lastName"] = data["last_name"]
    if "first_name" in data:
        payload["firstName"] = data["first_name"]
    if "email" in data:
        payload["email"] = data["email"]

    if "password" in data:
        password = data["password"]
        set_up_password(user_id, password, admin)

    return requests.request(
        "PUT", url=url, headers=headers, json=payload, verify=False
    ).status_code


def create_group(data, admin):
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/groups"
    token = get_token(admin)

    headers = {
        "content-type": "application/json",
        "Authorization": "Bearer " + str(token),
    }
    payload = {"name": data.get("id").strip().split("#")[-1]}

    return requests.request(
        "POST", url, json=payload, headers=headers, verify=False
    ).status_code


def delete_group(data, admin):
    group_name = data["id"]
    group_name = str(group_name).strip().split("#")[-1]

    group_id = get_group_id(group_name, admin)
    print(group_name, group_id)

    token = get_token(admin)

    headers = {
        "authorization": "Bearer " + str(token),
        "content-type": "application/json",
        "cache-control": "no-cache",
    }
    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = (
        f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/groups/"
        + str(group_id).strip()
    )

    return requests.delete(url=url, headers=headers).status_code


def create_member_group(data, admin):
    group_name = str(data["id"]).strip().split("#")[-1]
    user_name = str(data["sk"]).strip().split("#")[-1]

    user_id = get_user_id(user_name, admin)
    group_id = get_group_id(group_name, admin)

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]

    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}/groups/{group_id}"
    token = get_token(admin)

    headers = {
        "authorization": "Bearer " + str(token),
        "content-type": "application/json",
        "cache-control": "no-cache",
    }
    # payload = {
    #     "realms": "dev",
    #     "userID": user_id,
    #     "groupID": group_id
    # }
    # return requests.request("PUT", url=url, headers=headers,
    #                         json=payload, verify=False).status_code

    return requests.request("PUT", url=url, headers=headers).status_code


def delete_member_group(data, admin):
    group_name = str(data["id"]).strip().split("#")[-1]
    user_name = str(data["sk"]).strip().split("#")[-1]

    user_id = get_user_id(user_name, admin)
    group_id = get_group_id(group_name, admin)

    keycloak_url = admin["keycloak_url"]
    keycloak_realm = admin["keycloak_realm"]
    url = f"{keycloak_url}/auth/admin/realms/{keycloak_realm}/users/{user_id}/groups/{group_id}"
    token = get_token(admin)

    headers = {
        "authorization": "Bearer " + str(token),
        "content-type": "application/json",
        "cache-control": "no-cache",
    }
    return requests.request("DELETE", url=url, headers=headers).status_code


## ----------update to db---------------- ##


def create_data(table_name, data):
    print(f"create_data: {table_name}")
    print(f"create_data: {data}")
    # ignore if data is config#version
    sk = data["sk"]
    if "config#" in sk:
        return

    if "password" in data:
        del data["password"]

    client = boto3.client("dynamodb")
    client.put_item(TableName=table_name, Item=data)
    print("complete")


# def update_data(table_name, data):
#     # ignore if data is config#version
#     sk = data["sk"]
#     if "config#" in sk:
#         return

#     print(f"update_data: {table_name}")
#     print(f"update_data: {data}")
#     if "password" in data:
#         del data["password"]

#     client = boto3.client("dynamodb")
#     client.put_item(TableName=table_name, Item=data)


def delete_data(table_name, data):
    print(f"delete_data: {table_name}")
    print(f"delete_data: {data}")
    client = boto3.client("dynamodb")
    client.delete_item(TableName=table_name, Key=data)


def lambda_handler(event, context):
    print(f"process sqs event: {event}")
    system_name = os.environ.get("SYSTEM_NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")

    for record in event["Records"]:
        body = json.loads(record["body"])

        message = json.loads(body["Message"])
        sso_type = message.get("sso_type", "")
        if sso_type != "keycloak":
            continue

        for mess in message["infos"]:
            system_id, tenant_id = mess["system_id"], mess["tenant_id"]
            event_name = mess["event_name"]
            data = mess["data"]

            table_name = f"{system_name}_{env}_{system_id}_{tenant_id}_users"
            if event_name == "INSERT":
                create_data(table_name, data)
            elif event_name == "MODIFY":
                # update to db same to create data
                create_data(table_name, data)
            elif event_name == "REMOVE":
                delete_data(table_name, data)

    # TODO: sync data to keycloak
    for record in event["Records"]:
        body = json.loads(record["body"])

        message = json.loads(body["Message"])
        sso_type = message.get("sso_type", "")
        if sso_type != "keycloak":
            continue

        for mess in message["infos"]:
            system_id, tenant_id = mess["system_id"], mess["tenant_id"]
            event_name = mess["event_name"]
            data = mess["data"]
            region = os.environ.get("REGION", "ap-northeast-1")
            table_name = f"{system_name}_{env}_{system_id}_{tenant_id}_Config"

            table = boto3.resource(
                "dynamodb", region_name=region).Table(table_name)
            resp = table.get_item(
                Key={"system_id": system_id, "tenant_id": tenant_id})

            admin = resp.get("Item")

            if event_name == "INSERT":
                sk = str(data["sk"]).strip().split("#")[0]
                pk = str(data["id"]).strip().split("#")[0]
                if str(sk).strip() == "config":
                    if str(pk) == "user":
                        create_user(data, admin)
                    else:
                        create_group(data, admin)
                if sk == "member":
                    create_member_group(data, admin)
            elif event_name == "MODIFY":
                sk = str(data["sk"]).split("#")[0]
                pk = str(data["id"]).split("#")[0]
                if sk == "config":
                    if pk == "user":
                        update_user(data, admin)
            elif event_name == "REMOVE":
                sk = str(data["sk"]).strip().split("#")[0]
                pk = str(data["id"]).strip().split("#")[0]
                if str(sk).strip() == "config":
                    if str(pk)[:4] == "user":
                        delete_user(data, admin)
                    else:
                        delete_group(data, admin)
                if sk == "member":
                    delete_member_group(data, admin)

    # TODO: push to eventbridge

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
