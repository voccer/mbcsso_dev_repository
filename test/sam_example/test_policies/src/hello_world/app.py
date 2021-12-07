import json
import time


def lambda_handler(event, context):
    print("context")
    print(context)
    # print(context["authorizer"])
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
