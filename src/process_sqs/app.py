import os
import json
import boto3


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
        sso_type= message.get("sso_type","")
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

    ## TODO: sync data to keycloak
    
    ## TODO: push to eventbridge

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
