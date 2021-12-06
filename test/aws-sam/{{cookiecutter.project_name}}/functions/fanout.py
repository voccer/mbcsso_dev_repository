import boto3
import json
import os
import sys
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
cloudwatch_events = boto3.client("events")
table = boto3.resource(
    "dynamodb", region_name=os.environ.get("REGION", "us-east-2")
).Table(os.environ.get("TABLE_NAME", "test"))


def scan_table(table=table):
    response = table.scan()
    data = response["Items"]
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        data.extend(response["Items"])
    logger.info(data)
    return data


def put_user_events(users):
    event_count = 0
    entries = []
    for user in users:
        event_count += 1
        entries.append(
            {
                "DetailType": "EMAIL_AWS_RSS_INFO",
                "Source": "whatsnew.rss.fanout",
                "Detail": json.dumps(user),
            }
        )
        if event_count % 10 == 0:
            logger.info(entries)
            cloudwatch_events.put_events(Entries=entries)
            entries = []
    if entries:
        cloudwatch_events.put_events(Entries=entries)


def lambda_handler(event, context):
    logger.info(event)
    put_user_events(scan_table())
