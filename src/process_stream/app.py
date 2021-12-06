import os
import json
import boto3


def lambda_handler(event, context):
    infos = []

    for record in event["Records"]:
        info = {}
        info["event_name"] = record["eventName"]
        ddb_arn = record["eventSourceARN"]
        ddb_table_name = ddb_arn.split(":")[5].split("/")[
            1
        ]  # extract table name from ARN example: arn:aws:dynamodb:us-east-1:123456789012:table/mbcsso_dev_1_1_user_commands
        system_id, tenant_id = ddb_table_name.split("_")[
            2:4
        ]  # extract system_id and tenant_id from table name
        info["system_id"], info["tenant_id"] = system_id, tenant_id
        if record["eventName"] == "INSERT":
            info["data"] = record["dynamodb"]["NewImage"]

        elif record["eventName"] == "REMOVE":
            info["data"] = record["dynamodb"]["Keys"]

        elif record["eventName"] == "MODIFY":
            info["data"] = record["dynamodb"]["NewImage"]

        if "sso_type" in info["data"]:
            if info["data"]["sso_type"]["S"] != "keycloak":
                continue
            
        infos.append(info)

    topic_name = os.environ.get("TOPIC_NAME", "mbcsso_dev_topic")
    region = os.environ.get("REGION", "ap-northeast-1")
    account_id = os.environ.get("ACCOUNT_ID", "465316005105")

    client = boto3.client("sns")

    response = client.publish(
        TargetArn=f"arn:aws:sns:{region}:{account_id}:{topic_name}",
        Message=json.dumps({"default": json.dumps(infos)}),
        MessageStructure="json",
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
