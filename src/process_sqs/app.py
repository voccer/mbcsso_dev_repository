import os
import json
import boto3

import requests
import ast

from requests.api import head


def get_user_id(username):
    url = "https://dev.sso-service.com/auth/admin/realms/dev/users/?username=" + \
        str(username)

    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }

    return requests.get(url=url, headers=headers).json()[0]["id"]


def get_group_id(group_name):
    url = "https://dev.sso-service.com/auth/admin/realms/dev/groups?search=" + \
        str(group_name)

    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }

    return requests.get(url=url, headers=headers).json()[0]["id"]


def get_token():
    url = "https://dev.sso-service.com/auth/realms/master/protocol/openid-connect/token"

    params = {
        "client_id": "admin-cli",
        "username": "keycloak-developer",
        "password": "hA3Me3ub7jMJwc772TpUsB6f2Ccd",
        "grant_type": "password"
    }

    return ast.literal_eval(requests.post(url, params, verify=False).content.decode("utf-8"))['access_token']


def create_user(data):
    url = "https://dev.sso-service.com/auth/admin/realms/dev/users"
    username = data.get('id').strip().split("#")[-1]
    payload = {
        "enabled": True,
        "attributes": {},
        "groups": [],
        "emailVerified": "",
        "username": username
    }

    token = get_token()
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }

    if "first_name" in data:
        payload["firstName"] = data["first_name"]
    if "last_name" in data:
        payload["lastName"] = data["last_name"]

    return requests.post(url=url, headers=headers, json=payload, verify=False).status_code


def delete_user(data):
    username = data["id"]
    username = str(username).strip()[5:]

    user_id = get_user_id(username)

    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }

    url = "https://dev.sso-service.com/auth/admin/realms/dev/users/" + \
        str(user_id).strip()

    requests.delete(url=url, headers=headers)


def update_user(data):
    username = data.get('id').strip().split("#")[-1]

    user_id = get_user_id(username)

    url = f"https://dev.sso-service.com/auth/admin/realms/dev/users/{user_id}"

    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }
    payload = {
        "username": username
    }

    if "last_name" in data:
        payload["lastName"] = data["last_name"]
    if "first_name" in data:
        payload["firstName"] = data["first_name"]
    if "email" in data:
        payload["email"] = data["email"]

    return requests.request("PUT", url=url, headers=headers, json=payload, verify=False).status_code


def create_group(data):
    url = "https://dev.sso-service.com/auth/admin/realms/dev/groups"
    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }
    payload = {
        "name": data.get('id').strip()[6:]
    }

    return requests.request("POST", url, json=payload, headers=headers, verify=False).status_code


def delete_group(data):
    group_name = data["id"]
    group_name = str(group_name).strip()[6:]

    group_id = get_group_id(group_name)
    print(group_name, group_id)

    token = get_token()

    headers = {
        'authorization': 'Bearer ' + str(token),
        'content-type': "application/json",
        'cache-control': "no-cache",
    }

    url = "https://dev.sso-service.com/auth/admin/realms/dev/groups/" + \
        str(group_id).strip()

    return requests.delete(url=url, headers=headers).status_code


def create_member_group(data):
    group_name = str(data["id"]).strip()[6:]
    user_name = str(data["sk"]).strip()[7:]

    user_id = get_user_id(user_name)
    group_id = get_group_id(group_name)

    url = f"https://dev.sso-service.com/auth/admin/realms/dev/users/{user_id}/groups/{group_id}"
    token = get_token()

    headers = {
        'authorization': 'Bearer ' + str(token),
        'content-type': "application/json",
        'cache-control': "no-cache",
    }
    # payload = {
    #     "realms": "dev",
    #     "userID": user_id,
    #     "groupID": group_id
    # }
    # return requests.request("PUT", url=url, headers=headers,
    #                         json=payload, verify=False).status_code

    return requests.request("PUT", url=url, headers=headers).status_code


def delete_member_group(data):
    group_name = str(data["id"]).strip()[6:]
    user_name = str(data["sk"]).strip()[7:]

    user_id = get_user_id(user_name)
    group_id = get_group_id(group_name)

    url = f"https://dev.sso-service.com/auth/admin/realms/dev/users/{user_id}/groups/{group_id}"
    token = get_token()

    headers = {
        'authorization': 'Bearer ' + str(token),
        'content-type': "application/json",
        'cache-control': "no-cache",
    }
    return requests.request("DELETE", url=url, headers=headers).status_code


def create_data(table_name, data):
    print(f"create_data: {table_name}")
    print(f"create_data: {data}")
    # ignore if data is config#version
    sk = data["sk"]
    if "config#" in sk:
        return

    client = boto3.client("dynamodb")
    client.put_item(TableName=table_name, Item=data)
    print("complete")


def update_data(table_name, data):
    # ignore if data is config#version
    sk = data["sk"]
    if "config#" in sk:
        return

    print(f"update_data: {table_name}")
    print(f"update_data: {data}")

    client = boto3.client("dynamodb")
    client.put_item(TableName=table_name, Item=data)


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
                update_data(table_name, data)
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

            if event_name == "INSERT":
                sk = str(data["sk"]).strip().split("#")[0]
                pk = str(data["id"]).strip().split("#")[0]
                if str(sk).strip() == "config":
                    if str(pk) == "user":
                        create_user(data)
                    else:
                        create_group(data)
                if sk == "member":
                    create_member_group(data)
            elif event_name == "MODIFY":
                sk = str(data["sk"]).split("#")[0]
                pk = str(data["id"]).split("#")[0]
                if sk == "config":
                    if pk == "user":
                        update_user(data)
            elif event_name == "REMOVE":
                sk = str(data["sk"]).strip().split("#")[0]
                pk = str(data["id"]).strip().split("#")[0]
                if str(sk).strip() == "config":
                    if str(pk)[:4] == "user":
                        delete_user(data)
                    else:
                        delete_group(data)
                if sk == "member":
                    delete_member_group(data)

    # TODO: push to eventbridge

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
