import boto3
import json


def lambda_handler(message, context):
    logger.info("hello world")
    logger.info("message: {}".format(message))
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
