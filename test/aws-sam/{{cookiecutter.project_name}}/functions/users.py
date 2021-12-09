import boto3
import jsonschema
import json
import os
import sys
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

table = boto3.resource(
    "dynamodb", region_name=os.environ.get("REGION", "us-east-2")
).Table(os.environ.get("TABLE_NAME", "test"))
with open("services.json", "r") as f:
    SERVICES = json.load(f)
SERVICES_SCHEMA = {"type": "array", "items": {"type": "string", "enum": SERVICES}}
NEW_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
    },
    "required": ["username", "email"],
}
UPDATE_USER_SCHEMA = {
    "type": "object",
    "properties": {"email": {"type": "string", "format": "email"}},
    "required": ["email"],
}


def validate_schema(input, schema):
    validator = jsonschema.Draft4Validator(schema)
    errors = sorted(validator.iter_errors(input), key=lambda e: e.path)
    if errors:
        raise Exception("Invalid input! {}".format(errors))


def respond(err, res=None):
    return {
        "statusCode": "400" if err else "200",
        "body": err.message if err else json.dumps(res),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def getUser(username, table=table):
    resp = table.get_item(
        Key={"username": username}, AttributesToGet=["username", "email"]
    ).get("Item")
    return resp


def getUserServices(username, table=table):
    resp = table.get_item(Key={"username": username}, AttributesToGet=["services"]).get(
        "Item"
    )
    return resp


def postUser(input, table=table):
    validate_schema(input, NEW_USER_SCHEMA)
    input["services"] = []
    table.put_item(Item=input, ConditionExpression="attribute_not_exists(username)")
    return "Successfully saved new user"


def putUserServices(username, input, table=table):
    services = [x.lower() for x in input.get("services", [])]
    validate_schema(services, SERVICES_SCHEMA)
    existing = getUser(username, table=table)
    if input.get("action") == "ADD":
        services = list(set(services + existing["services"]))
    elif input.get("action") == "REMOVE":
        services = list(set(existing["services"]) - set(services))
    else:
        raise Exception("Unknown action '{}'".format(input.get("action")))
    table.update_item(
        Key={"username": username},
        UpdateExpression="SET services = :i",
        ExpressionAttributeValues={":i": services},
    )
    return "Successfully updated user services"


def putUser(username, input, table=table):
    validate_schema(input, UPDATE_USER_SCHEMA)
    table.update_item(
        Key={"username": username},
        UpdateExpression="SET email = :i",
        ExpressionAttributeValues={":i": input["email"]},
    )
    return "Successfully updated user"


def deleteUser(username, table=table):
    table.delete_item(Key={"username": username})
    return "Successfully deleted user"


def getServices():
    return SERVICES


def users_handler(event):
    operation = event["httpMethod"]
    if operation == "POST":
        return postUser(json.loads(event["body"]))
    else:
        raise ValueError("Unsupported method '{}'".format(operation))


def user_handler(event):
    operations = {"DELETE": deleteUser, "GET": getUser, "PUT": putUser}
    payload = [event["pathParameters"]["user"]]
    operation = event["httpMethod"]
    if operation == "PUT":
        payload.append(json.loads(event["body"]))
    if operation in operations:
        return operations[operation](*payload)
    else:
        raise ValueError("Unsupported method '{}'".format(operation))


def user_services_handler(event):
    operation = event["httpMethod"]
    if operation == "PUT":
        return putUserServices(
            event["pathParameters"]["user"], json.loads(event["body"])
        )
    elif operation == "GET":
        return getUserServices(event["pathParameters"]["user"])
    else:
        raise ValueError("Unsupported method '{}'".format(operation))


def services_handler(event):
    operation = event["httpMethod"]
    if operation == "GET":
        return getServices()
    else:
        raise ValueError("Unsupported method '{}'".format(operation))


def lambda_handler(event, context):
    logger.info("Received event: " + json.dumps(event, indent=2))

    resource_paths = {
        "/services": services_handler,
        "/users": users_handler,
        "/users/{user}": user_handler,
        "/users/{user}/services": user_services_handler,
    }

    resource_path = event["requestContext"]["resourcePath"]
    if resource_path in resource_paths:
        try:
            return respond(None, resource_paths[resource_path](event))
        except Exception as e:
            return respond(e)
    else:
        return respond(
            ValueError('Unsupported resource path "{}"'.format(resource_path))
        )
