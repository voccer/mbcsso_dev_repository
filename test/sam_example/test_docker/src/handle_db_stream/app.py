import boto3
import json


def lambda_handler(event, context):
    # region_name = "ap-northeast-1"
    # table_name = "UserTable"
    # user_table = boto3.resource("dynamodb", region_name)
    # table = user_table.Table(table_name)
    for record in event["Records"]:
        print(record["eventID"])
        print(record["eventName"])
    print("Successfully processed %s records." % str(len(event["Records"])))

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
            }
        ),
    }
