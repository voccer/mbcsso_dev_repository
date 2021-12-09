import os
import json
import boto3


def lambda_handler(event, context):
    print(f"Process stream event: {event}")
    infos = []
    system_name = os.environ.get("SYSTEM_NAME")
    env = os.environ.get("ENV")
    prefix = f"{system_name}_{env}"
    for record in event["Records"]:
        info = {}
        ddb_arn = record["eventSourceARN"]
        ddb_table_name = ddb_arn.split(":")[5].split("/")[
            1
        ]  # extract table name from ARN example: arn:aws:dynamodb:us-east-1:123456789012:table/mbcsso_dev_1_1_user_commands
        system_id, tenant_id = ddb_table_name.replace(prefix, "").split("_")[
            1:3
        ]  # extract system_id and tenant_id from table name
        info["system_id"], info["tenant_id"] = system_id, tenant_id
        info["event_name"] = record["eventName"]

        if record["eventName"] == "INSERT":
            info["data"] = record["dynamodb"]["NewImage"]

        elif record["eventName"] == "REMOVE":
            info["data"] = record["dynamodb"]["Keys"]

        elif record["eventName"] == "MODIFY":
            info["data"] = record["dynamodb"]["NewImage"]

        if "data" in info:
            infos.append(info)

    print(f"Process stream infos: {infos}")

    topic_name = os.environ.get("TOPIC_NAME")
    region = os.environ.get("REGION")
    account_id = os.environ.get("ACCOUNT_ID")

    client = boto3.client("sns")

    response = client.publish(
        TargetArn=f"arn:aws:sns:{region}:{account_id}:{topic_name}",
        Message=json.dumps({"default": json.dumps(infos)}),
        MessageStructure="json",
        MessageAttributes={
            "sso_type": {"DateType": "String", "StringValue": "keycloak"}
        },
    )

    print(f"Publish to {topic_name} with response:: {response}")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
