import os
import boto3
from boto3.dynamodb.conditions import Key, Attr


def get_query_table_name(system_id, tenant_id):
    name = os.environ.get("SYSTEM_NAME", "mbcsso")
    env = os.environ.get("ENV", "dev")
    return f"{name}_{env}_{system_id}_{tenant_id}_users"


def get_command_table_name(system_id, tenant_id):
    name = os.environ.get("SYSTEM_NAME", "mcbsso")
    env = os.environ.get("ENV", "dev")
    return f"{name}_{env}_{system_id}_{tenant_id}_user_commands"


def check_user_exist(user_id, table):
    user_resp = table.get_item(
        Key={"id": f"user#{user_id}", "sk": "config"})
    user_item = user_resp.get("Item", None)
    if user_item:
        is_active = user_item.get("is_active")
        if is_active:
            return True
    return False


def check_group_exist(group_id, table):
    group_resp = table.get_item(
        Key={"id": f"group#{group_id}", "sk": "config"})

    group_item = group_resp.get("Item", None)
    if group_item:
        is_active = group_item.get("is_active")
        if is_active:
            return True
    return False


def check_email_exist(email, table):
    email_resp = table.query(
        IndexName="UserEmailGSI",
        KeyConditionExpression=Key("email").eq(email)
        & Key("sk").eq("config"),
    )

    if email_resp.get("Count") > 0:
        is_active = email_resp.get("Items")[0].get("is_active", "")
        if str(is_active).strip() == 1:
            return True
    return False


def check_member_group(user_id, group_id, table):
    member_resp = table.get_item(
        Key={"id": f"group#{group_id}", "sk": f"member#{user_id}"}
    )

    member_item = member_resp.get("Item", None)
    if member_item:
        return True
    return False
