import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def create_sso(event):
    name = os.environ.get("NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")
    region = os.environ.get("REGION", "ap-northeast-1")
    body = json.loads(event["body"])
    system_id = body["system_id"]
    tenant_id = body["tenant_id"]

    config_table_name = "{}_{}_Config".format(name, env)
    user_commands_table_name = "{}_{}_{}_{}_user_commands".format(
        name, env, system_id, tenant_id
    )
    users_table_name = "{}_{}_{}_{}_users".format(name, env, system_id, tenant_id)

    dynamodb = boto3.resource("dynamodb", region_name=region)

    ## create table
    users_table = dynamodb.create_table(
        TableName=users_table_name,
        KeySchema=[
            {"AttributeName": "year", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
        ],
        AttributeDefinitions=[
            {"AttributeName": "year", "AttributeType": "N"},
            {"AttributeName": "title", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
    )
    user_commands_table = dynamodb.create_table(
        TableName=user_commands_table_name,
        KeySchema=[
            {"AttributeName": "year", "KeyType": "HASH"},  # Partition key
            {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
        ],
        AttributeDefinitions=[
            {"AttributeName": "year", "AttributeType": "N"},
            {"AttributeName": "title", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 10, "WriteCapacityUnits": 10},
    )
    config_table = dynamodb.Table(config_table_name)
    params = {"system_id": system_id, "tenant_id": tenant_id}
    response = config_table.put_item(TableName=config_table_name, Item=params)
    print("response")
    print(response)
    
    return


def lambda_handler(event, context):
    # logger.info("Received event: " + json.dumps(event, indent=2))

    create_sso(event)
    return json.dumps({"msg": "Sso created"})

    # resource_paths = {
    #     "/sso": create_sso,
    # "/sso/{id}": update_sso,
    # "/sso/{id}": delete_sso,
    # }

    # resource_path = event["requestContext"]["resourcePath"]
    # if resource_path in resource_paths:
    #     try:
    #         return respond(None, resource_paths[resource_path](event))
    #     except Exception as e:
    #         return respond(e)
    # else:
    #     return respond(
    #         ValueError('Unsupported resource path "{}"'.format(resource_path))
    #     )

    # return response
