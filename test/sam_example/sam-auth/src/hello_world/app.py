import boto3
import json


def lambda_handler(message, context):
    print("hello world")
    print("message: {}".format(message))
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
