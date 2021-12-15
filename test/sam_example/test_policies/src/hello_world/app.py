import json
import time


def lambda_handler(event, context):
    logger.info("context")
    logger.info(context)
    # logger.info(context["authorizer"])
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
