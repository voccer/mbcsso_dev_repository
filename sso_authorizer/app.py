def lambda_handler(event, context):
    response = {
        "isAuthorized": False,
        "context": {
            "stringKey": "value",
            "numberKey": 1,
            "booleanKey": True,
            "arrayKey": ["value1", "value2"],
            "mapKey": {"value1": "value2"},
        },
    }

    if event["headers"]["authorization"] == "secretToken":
        response = {
            "isAuthorized": True,
            "context": {
                "stringKey": "value",
                "numberKey": 1,
                "booleanKey": True,
                "arrayKey": ["value1", "value2"],
                "mapKey": {"value1": "value2"},
            },
        }

    return response
