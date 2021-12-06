import os
import json
import time
import logging

import boto3
from boto3.dynamodb.conditions import Key, Attr
from aws_xray_sdk.core import xray_recorder
import cryptocode

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


@xray_recorder.capture("create user")
def create_user(event, table):
    body = json.loads(event["body"])

    if "username" not in body:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "username required"}),
        }

    user_id = body["username"]
    check_user = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})

    if check_user.get("Item", None):
        is_active = check_user["Item"].get("is_active", "")
        if str(is_active).strip() == "1":
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"code": "E_INVALID", "message": "user name already exist"}
                ),
            }

    params = {
            "id": "user#" + body["username"],
            "sk": "config",
            "command": "add",
            "sso_type": "keycloak",
            "is_active": 1,
            "version": 1,
            "updated_at": int(time.time()),
        }
    
    if "email" in body:
        params["email"] = body["email"]
        
        check_email = table.query(
            IndexName="UserEmailGSI",
            KeyConditionExpression=Key("email").eq(params["email"]) & Key("sk").eq("config"),
        )
        if check_email.get("Count") > 0:
            is_active = check_email["Items"][0].get("is_active", "")
            if str(is_active).strip() == "1":
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {"code": "E_INVALID", "message": "email already exist"}
                    ),
                }

    if "password" in body:
        params["password"] = body["password"]  # ToDo: encrypt password
    if "first_name" in body:
        params["first_name"] = body["first_name"]
    if "last_name" in body:
        params["last_name"] = body["last_name"]

    passwd = cryptocode.encrypt(params["password"], 'password')
    params["password"] = passwd
    
    try:
        table.put_item(Item=params)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"code": "error", "message": str(e)}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "create user"}),
    }


@xray_recorder.capture("update user")
def update_user(event, table):
    body = json.loads(event["body"])

    if "username" in body:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "username not edit"}),
        }

    raw_path = event.get("rawPath", None)
    if raw_path is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }

    user_id = raw_path.split("/")[-1]
    check_user = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})

    if check_user.get("Item", None):
        is_active = check_user["Item"].get("is_active", "")
        if str(is_active).strip() != "1":
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "user not exist"}),
            }
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "user not exist"}),
        }
    user = check_user.get("Item")

    current_version = user.get("version")

    params = {
        "id": f"user#{user_id}",
        "sk": "config",
        "command": "update",
        "sso_type": "keycloak",
        "is_active": 1,
        "version": f"{int(current_version) + 1}",
        "updated_at": int(time.time()),
    }

    if "email" in body:
        params["email"] = body["email"]
        email = params["email"]
        check_email = table.query(
            IndexName="UserEmailGSI",
            KeyConditionExpression=Key("email").eq(email) & Key("sk").eq("config"),
        )
        if check_email.get("Count") > 0:
            is_active = check_email["Items"][0].get("is_active", "")
            if str(is_active).strip() == "1":
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {"code": "E_INVALID", "message": "email already exist"}
                    ),
                }
    else:
        params["email"] = user.get("email", "")

    
    params["password"] = body.get("password", user.get("password", ""))
    params["first_name"] = body.get("first_name", user.get("first_name", ""))
    params["last_name"] = body.get("last_name", user.get("last_name", ""))

    ExpressionAttributeValues = {
        ":c": "update",
        ":s": f"{int(current_version) + 1}",
        ":fn": params["first_name"],
        ":ln": params["last_name"],
        ":p": params["password"],
        ":e": params["email"],
        ":u": int(time.time()),
    }
    for k, v in list(ExpressionAttributeValues.items()):
        if v is None:
            del ExpressionAttributeValues[k]

    # add new record for command update, current record will add new record
    table.update_item(
        Key={"id": f"user#{user_id}", "sk": "config"},
        UpdateExpression="SET command = :c, version = :s, first_name = :fn, last_name = :ln, password = :p, email = :e, updated_at = :u",
        ExpressionAttributeValues=ExpressionAttributeValues,
        ReturnValues="UPDATED_NEW",
    )

    try:
        user["sk"] = f"config#{current_version}"
        table.put_item(Item=user)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"code": "error", "message": str(e)}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "update user"}),
    }


@xray_recorder.capture("delete user")
def delete_user(event, table):
    raw_path = event.get("rawPath", None)
    if raw_path is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }

    user_id = raw_path.split("/")[-1]

    check_user = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})
    if check_user.get("Item", None) is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }
    else:
        is_active = check_user.get("Item").get("is_active", "")
        if str(is_active).strip() != "1":
<<<<<<< HEAD:src/command/app.py
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
            }
=======
            return {"statusCode": 400, "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"})}
>>>>>>> 6ef41dc34a2e8ec9b8fbb1dcebc73b0e6be89839:command/app.py

    user = check_user.get("Item")
    current_version = user["version"]

    # delete linked user group
    resp = table.query(
        IndexName="UserGroupGSI",
<<<<<<< HEAD:src/command/app.py
        KeyConditionExpression=Key("sk").eq(f"memeber#{user_id}")
        & Key("id").begins_with("group#"),
=======
        KeyConditionExpression=Key('sk').eq(
            f"memeber#{user_id}") & Key('id').begins_with('group#')
>>>>>>> 6ef41dc34a2e8ec9b8fbb1dcebc73b0e6be89839:command/app.py
    )

    items = resp.get("Items", None)
    if items is not None:
        for item in items:
            pk = item["id"]
            sk = f"memeber#{user_id}"
<<<<<<< HEAD:src/command/app.py
            table.delete_item(Key={"id": pk, "sk": sk})
=======
            table.delete_item(
                Key={"id": pk, "sk": sk})
>>>>>>> 6ef41dc34a2e8ec9b8fbb1dcebc73b0e6be89839:command/app.py

    # update current record to config#version
    user["sk"] = f"config#{current_version}"
    table.put_item(Item=user)
    resp = table.update_item(
        Key={"id": f"user#{user_id}", "sk": "config"},
        UpdateExpression="SET is_active = :r, command = :c, updated_at = :u, version = :v",
        ExpressionAttributeValues={
            ":r": "",
            ":c": "delete",
            ":v": f"{int(current_version) + 1}",
            ":u": int(time.time()),
        },
        ReturnValues="UPDATED_NEW",
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "delete user"}),
    }


@xray_recorder.capture("create group")
def create_group(event, table):
    body = json.loads(event["body"])
    if "groupname" not in body:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "group_name required"}),
        }

    group_id = body["groupname"]
    check_group = table.get_item(Key={"id": f"group#{group_id}", "sk": "config"})

    if check_group.get("Item", None):
        is_active = check_group.get("is_active", "")
        if str(is_active).strip() == "1":
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {"code": "E_INVALID", "message": "group name already exist"}
                ),
            }

    params = {
        "id": "group#" + body["groupname"],
        "sk": "config",
        "command": "add",
        "sso_type": "keycloak",
        "is_active": 1,
        "version": 1,
        "updated_at": int(time.time()),
    }
    if "description" in body:
        params["description"] = body["description"]

    try:
        table.put_item(Item=params)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"code": "error", "message": str(e)}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "create group"}),
    }


@xray_recorder.capture("update group")
def update_group(event, table):
    body = json.loads(event["body"])

    if "groupname" in body:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "groupname not edit"}),
        }

    if "description" not in body:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"code": "E_INVALID", "message": "description required"}
            ),
        }

    raw_path = event.get("rawPath", None)
    if raw_path is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }

    group_id = raw_path.split("/")[-1]
    check_group = table.get_item(Key={"id": f"group#{group_id}", "sk": "config"})

    if check_group.get("Item", None):
        is_active = check_group["Item"].get("is_active", "")
        if str(is_active).strip() != "1":
            print("check_group:: not active")
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
            }
    else:
        print("check_group:: not exist")
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
        }
    group = check_group.get("Item")

    current_version = group.get("version")

    # add new record for command update, current record will add new record
    table.update_item(
        Key={"id": f"group#{group_id}", "sk": "config"},
        UpdateExpression="SET command = :c, version = :s, description = :d, updated_at = :u",
        ExpressionAttributeValues={
            ":c": "update",
            ":s": f"{int(current_version) + 1}",
            ":d": body["description"],
            ":u": int(time.time()),
        },
        ReturnValues="UPDATED_NEW",
    )

    try:
        group["sk"] = f"config#{current_version}"
        table.put_item(Item=group)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"code": "error", "message": str(e)}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "update group"}),
    }


@xray_recorder.capture("delete group")
def delete_group(event, table):
    raw_path = event.get("rawPath", None)
    if raw_path is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }

    group_id = raw_path.split("/")[-1]

    check_group = table.get_item(Key={"id": f"group#{group_id}", "sk": "config"})
    if check_group.get("Item", None) is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }
    else:
        is_active = check_group.get("Item").get("is_active", "")
        if str(is_active).strip() != "1":
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
            }
    group = check_group.get("Item")
    current_version = group["version"]

    resp = table.query(
<<<<<<< HEAD:src/command/app.py
        KeyConditionExpression=Key("id").eq(f"group#{group_id}")
        & Key("sk").begins_with("member#")
=======
        KeyConditionExpression=Key('id').eq(
            f"group#{group_id}") & Key('sk').begins_with('member#')
>>>>>>> 6ef41dc34a2e8ec9b8fbb1dcebc73b0e6be89839:command/app.py
    )

    items = resp.get("Items", None)
    if items is not None:
        for item in items:
            pk = item["id"]
            sk = item["sk"]
<<<<<<< HEAD:src/command/app.py
            table.delete_item(Key={"id": pk, "sk": sk})
=======
            table.delete_item(
                Key={"id": pk, "sk": sk})
>>>>>>> 6ef41dc34a2e8ec9b8fbb1dcebc73b0e6be89839:command/app.py

    # update current record to config#version
    group["sk"] = f"config#{current_version}"
    table.put_item(Item=group)

    res = table.update_item(
<<<<<<< HEAD:src/command/app.py
        Key={"id": f"group#{group_id}", "sk": "config"},
=======
        Key={
            "id": f"group#{group_id}",
            "sk": "config"
        },
>>>>>>> 6ef41dc34a2e8ec9b8fbb1dcebc73b0e6be89839:command/app.py
        UpdateExpression="SET is_active = :r, command = :c, updated_at = :u, version = :v",
        ExpressionAttributeValues={
            ":r": "",
            ":c": "delete",
            ":v": f"{int(current_version) + 1}",
            ":u": int(time.time()),
        },
        ReturnValues="UPDATED_NEW",
    )
    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "delete group"}),
    }


@xray_recorder.capture("add group member")
def add_group_member(event, table):
    print("start::")
    path_params = event.get("pathParameters", "")
    print(f"params:: {path_params}")
    if path_params == "":
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }
    if "user_id" not in path_params or "group_id" not in path_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }

    user_id = path_params["user_id"]
    group_id = path_params["group_id"]

    print("pass get infor")

    check_user = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})
    check_group = table.get_item(Key={"id": f"group#{group_id}", "sk": "config"})

    if check_group.get("Item", None):
        is_active = check_group["Item"].get("is_active", "")
        if str(is_active).strip() != "1":
            print("check_group:: not active")
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
            }
    else:
        print("check_group:: not exist")
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
        }

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

    params = {
        "id": f"group#{group_id}",
        "sk": f"member#{user_id}",
    }
    resp = table.get_item(Key=params)
    if resp.get("Item", None) is not None:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"code": "E_INVALID", "message": "user already exist in group"}
            ),
        }
    params["sso_type"] = "keycloak"
    params["updated_at"] = int(time.time())
    table.put_item(Item=params)
    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "add group member"}),
    }


@xray_recorder.capture("delete group member")
def delete_group_member(event, table):
    print("start::")
    path_params = event.get("pathParameters", "")
    print(f"params:: {path_params}")
    if path_params == "":
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }
    if "user_id" not in path_params or "group_id" not in path_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "Input invalid"}),
        }

    user_id = path_params["user_id"]
    group_id = path_params["group_id"]

    print("pass get infor")

    check_user = table.get_item(Key={"id": f"user#{user_id}", "sk": "config"})
    check_group = table.get_item(Key={"id": f"group#{group_id}", "sk": "config"})

    if check_group.get("Item", None):
        is_active = check_group["Item"].get("is_active", "")
        if str(is_active).strip() != "1":
            print("check_group:: not active")
            return {
                "statusCode": 400,
                "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
            }
    else:
        print("check_group:: not exist")
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "group not exist"}),
        }

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

    check_member = table.get_item(
        Key={"id": f"group#{group_id}", "sk": f"member#{user_id}"}
    )
    if check_member.get("Item", None) is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"code": "E_INVALID", "message": "user not in group"}),
        }

    resp = table.delete_item(Key={"id": f"group#{group_id}", "sk": f"member#{user_id}"})
    return {
        "statusCode": 200,
        "body": json.dumps({"code": "ok", "message": "delete member group"}),
    }


@xray_recorder.capture("CUD user/group")
def lambda_handler(event, context):
    logger.info(event)
    name = os.environ.get("SYSTEM_NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")
    region = os.environ.get("REGION", "ap-northest-1")
    authorizer_lambda = event["requestContext"]["authorizer"]["lambda"]
    system_id = authorizer_lambda["system_id"]
    tenant_id = authorizer_lambda["tenant_id"]

    user_commands_table_name = f"{name}_{env}_{system_id}_{tenant_id}_user_commands"

    user_commands_table = boto3.resource("dynamodb", region_name=region).Table(
        user_commands_table_name
    )

    route_key = event["requestContext"]["routeKey"]

    [method, path] = route_key.split(" ")

    if method == "POST" and path == "/users":
        return create_user(event, table=user_commands_table)
    elif method == "PUT" and path == "/users/{user_id}":
        return update_user(event, table=user_commands_table)
    elif method == "DELETE" and path == "/users/{user_id}":
        return delete_user(event, table=user_commands_table)
    elif method == "POST" and path == "/groups":
        return create_group(event, table=user_commands_table)
    elif method == "PUT" and path == "/groups/{group_id}":
        return update_group(event, table=user_commands_table)
    elif method == "DELETE" and path == "/groups/{group_id}":
        return delete_group(event, table=user_commands_table)
    elif method == "PUT" and path == "/users/{user_id}/groups/{group_id}":
        return add_group_member(event, table=user_commands_table)
    elif method == "DELETE" and path == "/users/{user_id}/groups/{group_id}":
        return delete_group_member(event, table=user_commands_table)
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Not found"}),
        }
    # resource_paths = {
    #     "/users": search_user,
    #     "/users{user_id}": get_user,
    #     "/users/{user}": user_handler,
    #     "/users/{user}/services": user_services_handler,
    # }

    # resource_path = event["requestContext"]["resourcePath"]
    # if resource_path in resource_paths:
    #     try:
    #         return respond(None, resource_paths[resource_path](event))
    #     except Exception as e:
    #         return respond(e)
    # else:
    #     return respond(
    #         ValueError('Unsupported resource path "{}"'.format(resource_path))
    #     )
