import sys

sys.path.append("functions")
import users
import json
import unittest
import boto3
from moto import mock_dynamodb2


class TestDynamo(unittest.TestCase):
    def setUp(self):
        pass

    @mock_dynamodb2
    def test_routes(self):
        dynamodb = boto3.resource("dynamodb", region_name="us-east-2")

        dynamodb.create_table(
            TableName="test",
            KeySchema=[
                {"AttributeName": "username", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        table = dynamodb.Table("test")

        # Test GET services
        services = [
            "ec2",
            "s3",
            "lambda",
            "ebs",
            "rds",
            "sagemaker",
            "iot",
            "fargate",
            "route-53",
            "workdocs",
            "sumerian",
            "gamelift",
            "batch",
            "elastic-beanstalk",
            "cloudformation",
            "cloudwatch",
            "cloudfront",
            "cloudtrail",
            "config",
            "step-functions",
            "swf",
            "ses",
            "sns",
            "sqs",
            "ses",
            "vpc",
            "sam",
            "pinpoint",
            "x-ray",
            "snowball",
        ]
        result = users.getServices()
        self.assertEquals(result, services)

        # Test POST new user
        body = {"email": "test@test.co", "username": "testuser"}
        result = users.postUser(body, table)
        self.assertEquals(result, "Successfully saved new user")

        # Test PUT user
        body = {"email": "test@test.com"}
        result = users.putUser("testuser", body, table)
        self.assertEquals(result, "Successfully updated user")

        # Test PUT user services (add)
        body = {"services": ["CloudWatch", "EC2", "SES"], "action": "ADD"}
        result = users.putUserServices("testuser", body, table)
        self.assertEquals(result, "Successfully updated user services")

        # Test PUT user services (remove)
        body = {"services": ["SES"], "action": "REMOVE"}
        result = users.putUserServices("testuser", body, table)
        self.assertEquals(result, "Successfully updated user services")

        # Test GET user
        result = users.getUser("testuser", table)
        self.assertEquals(result["username"], "testuser")
        self.assertEquals(result["email"], "test@test.com")

        # Test GET user services
        result = users.getUserServices("testuser", table)
        self.assertEquals(result["services"], ["ec2", "cloudwatch"])

        # Test DELETE
        result = users.deleteUser("testuser", table)
        self.assertEquals(result, "Successfully deleted user")


if __name__ == "__main__":
    unittest.main()
