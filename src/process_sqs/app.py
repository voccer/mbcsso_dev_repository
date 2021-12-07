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
    username = data.get('id').strip()[5:]
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

    return requests.post(url, headers, payload, verify=False)


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
    pass


def create_group(data):
    url = "https://dev.sso-service.com/auth/admin/realms/dev/groups"
    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }
    payload = {
        "name": data.get('id').strip()[:5]
    }

    requests.post(url=url, data=payload, headers=headers)


def delete_group(data):
    group_name = data["id"]
    group_name = str(group_name).strip()[6:]

    group_id = get_group_id(group_name)
    print(group_name, group_id)

    token = get_token()

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + str(token)
    }

    url = "https://dev.sso-service.com/auth/admin/realms/dev/groups/" + \
        str(group_id).strip()

    return requests.delete(url=url, headers=headers).status_code


def update_group(data):
    pass


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
                sk = data["sk"]
                pk = data["id"]
                if str(sk).strip() == "config":
                    if str(pk)[:4] == "user":
                        create_user(data)
                    else:
                        create_group(data)
            elif event_name == "MODIFY":
                pass
            elif event_name == "REMOVE":
                pass

    # TODO: push to eventbridge

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
