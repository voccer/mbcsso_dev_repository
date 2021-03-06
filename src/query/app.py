import os
import json
import logging

import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_xray_sdk.core import xray_recorder

from shared_code.logger import Logger
from shared_code.utils import get_query_table_name

logger = Logger().get_logger()


@xray_recorder.capture("get user")
def get_user(event, table):
    path_params = event.get("pathParameters")
    logger.info(f"params:: {path_params}")

    user_id = path_params["user_id"]
    user_id = str(user_id).lower()

    resp = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})

    item = resp.get("Item", None)

    if item is None:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"code": "E_INVALID", "message": "User not found or inactive"}
            ),
        }
    else:
        is_active = item.get("is_active", None)
        if is_active is None or str(is_active) != "1":
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"code": "E_INVALID", "message": "User not found or inactive"}
                ),
            }
        else:
            data = {"id": f"{user_id}"}
            data["email"] = item.get("email", "")
            data["first_name"] = item.get("first_name", "")
            data["last_name"] = item.get("last_name", "")
            data["attributes"] = item.get("attributes", {})

            return {"statusCode": 200, "body": json.dumps({"code": "ok", "data": data})}


@xray_recorder.capture("search user")
def search_user(event, table):
    items = []
    query_params = event["queryStringParameters"]
    logger.info(f"query:: {query_params}")

    if "username" in query_params:
        user_id = query_params["username"]
        user_id = str(user_id).lower()
        logger.info(f"username:: {user_id}")
        resp = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})
        if resp.get("Item", None) is not None:
            items.append(resp["Item"])
    elif "email" in query_params:
        email = query_params["email"]
        logger.info(f"email:: {email}")
        resp = table.query(
            IndexName="UserEmailGSI",
            KeyConditionExpression=Key("email").eq(
                email) & Key("sk").eq("config"),
        )
        if resp.get("Items", None) is not None:
            items = resp["Items"]
    elif "first_name" in query_params:
        first_name = query_params["first_name"]
        logger.info(f"first_name:: {first_name}")
        resp = table.query(
            IndexName="UserFirstNameGSI",
            KeyConditionExpression=Key("first_name").eq(first_name),
            ScanIndexForward=False,
        )

        if resp.get("Items", None) is not None:
            items = resp["Items"]
    elif "last_name" in query_params:
        last_name = query_params["last_name"]
        logger.info(f"last_name:: {last_name}")
        resp = table.query(
            IndexName="UserLastNameGSI",
            KeyConditionExpression=Key("last_name").eq(last_name),
            ScanIndexForward=False,
        )

        if resp.get("Items", None) is not None:
            items = resp["Items"]
    elif "last_name_contains" in query_params:
        last_name_contains = query_params["last_name_contains"]
        logger.info(f"last_name_contains:: {last_name_contains}")
        resp = table.scan(
            IndexName="UserLastNameGSI",
            FilterExpression=Attr("last_name").begins_with(last_name_contains),
        )
        items = resp["Items"]
    elif "first_name_contains" in query_params:
        first_name_contains = query_params["first_name_contains"]
        logger.info(f"first_name_contains:: {first_name_contains}")
        resp = table.scan(
            IndexName="UserFirstNameGSI",
            FilterExpression=Attr("first_name").begins_with(
                first_name_contains),
        )
        items = resp["Items"]
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }
    items_resp = []

    for item in items:
        is_active = item.get("is_active", None)
        if is_active:
            item_filter = {"id": item.get("id").replace("user#", "")}
            item_filter["email"] = item.get("email", "")
            item_filter["first_name"] = item.get("first_name", "")
            item_filter["last_name"] = item.get("last_name", "")
            item_filter["attributes"] = item.get("attributes", {})

            items_resp.append(item_filter)

    logger.info(f"item_resp:: {items_resp}")

    return {"statusCode": 200, "body": json.dumps({"code": "ok", "data": items_resp})}


@xray_recorder.capture("search group")
def search_group(event):
    return {"statusCode": 200, "body": json.dumps({"msg": "search group"})}


@xray_recorder.capture("get group")
def get_group(event, table):
    path_params = event.get("pathParameters")
    logger.info(f"params:: {path_params}")

    group_id = path_params["group_id"]
    group_id = str(group_id).lower()

    logger.info("pass get infor")

    check_group = table.get_item(
        Key={"id": f"group#{group_id}", "sk": "config"})

    if check_group.get("Item", None):
        is_active = check_group["Item"].get("is_active", "")
        if str(is_active).strip() != "1":
            logger.info("check_group:: not active")
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
            }
    else:
        logger.info("check_group:: not exist")
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
        }

    group = check_group.get("Item")
    group_resp = {"groupname": f"group_id"}
    group_resp["description"] = group.get("description", "")

    return {"statusCode": 200, "body": json.dumps({"code": "ok", "data": group_resp})}


@xray_recorder.capture("search user_group")
def search_user_group(event, table):
    path_params = event.get("pathParameters", "")
    logger.info(f"params:: {path_params}")
    user_id = path_params["user_id"]
    user_id = str(user_id).lower()

    check_user = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})
    if check_user.get("Item", None) is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "user not exist"}),
        }
    else:
        is_active = check_user.get("Item").get("is_active", "")
        if str(is_active).strip() != "1":
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "user invalid"}),
            }

    resp = table.query(
        IndexName="UserGroupGSI",
        KeyConditionExpression=Key("member_id").eq(f"member#{user_id}")
        & Key("id").begins_with("group#"),
    )
    items = resp.get("Items", None)
    logger.info(f"Items:: {items}")
    data = []
    if items is not None:
        for item in items:
            pk = item["id"]
            sk = f"config"
            logger.info(f"id:: {pk}, sk:: {sk}")
            group_resp = table.get_item(Key={"id": pk, "sk": sk})
            group = group_resp.get("Item", None)
            if group is not None:
                data.append(
                    {
                        "groupname": group["id"][6:],
                        "description": group.get("description", ""),
                    }
                )
    return {"statusCode": 200, "body": json.dumps({"code": "ok", "data": data})}


@xray_recorder.capture("get user/group")
def lambda_handler(event, context):
    logger.info(event)

    # name = os.environ.get("SYSTEM_NAME")
    # env = os.environ.get("ENV")

    region = os.environ.get("REGION")
    authorizer_lambda = event["requestContext"]["authorizer"]["lambda"]

    system_id, tenant_id = (
        authorizer_lambda["system_id"],
        authorizer_lambda["tenant_id"],
    )

    # user_query_table_name = f"{name}_{env}_{system_id}_{tenant_id}_users"
    user_query_table_name = get_query_table_name(system_id, tenant_id)

    user_query_table = boto3.resource("dynamodb", region_name=region).Table(
        user_query_table_name
    )

    route_key = event["requestContext"]["routeKey"]

    [method, path] = route_key.split(" ")

    if method == "GET":
        if path == "/users":
            return search_user(event, table=user_query_table)
        elif path == "/groups":
            return search_group(event, table=user_query_table)
        elif path == "/users/{user_id}":
            return get_user(event, table=user_query_table)
        elif path == "/groups/{group_id}":
            return get_group(event, table=user_query_table)
        elif path == "/users/{user_id}/groups":
            return search_user_group(event, table=user_query_table)
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Not found"}),
            }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Not found"}),
        }
