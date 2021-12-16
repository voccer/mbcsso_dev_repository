from config import config

from src.authorizer import app as authorizer_app
from src.command import app as command_app
from src.query import app as query_app
from src.process_stream import app as process_stream_app
from src.process_sqs import app as process_sqs_app
from src.process_wait import app as process_wait_app


def lambda_handler(event, context):
    if config["FUNCTION_NAME"] == "auth":
        return authorizer_app.lambda_handler(event, context)
    elif config["FUNCTION_NAME"] == "command":
        return command_app.lambda_handler(event, context)
    elif config["FUNCTION_NAME"] == "query":
        return query_app.lambda_handler(event, context)
    elif config["FUNCTION_NAME"] == "process_sqs":
        return process_sqs_app.lambda_handler(event, context)
    elif config["FUNCTION_NAME"] == "process_stream":
        return process_stream_app.lambda_handler(event, context)
    elif config["FUNCTION_NAME"] == "process_wait":
        return process_wait_app.lambda_handler(event, context)
