import os

config = {
    "ENV": os.environ.get("ENV") or "local",  # local, dev, stage, prod
    "FUNCTION_NAME": os.environ.get("FUNCTION_NAME")
    or "auth",  # auth, command, query, process_sqs, process_stream, process_wait
}