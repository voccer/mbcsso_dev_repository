# AWS News API: An Adventure with AWS SAM + GitLab CI

## Overview

This project has two purposes.

First and foremost, it's a fully functional (and, we hope, useful) serverless app! It's designed to email you weekly summaries of relevant updates about AWS services that you curate through a REST API. No more parsing through the blizzard of AWS feature announcements: just get simple updates about EC2, or CloudFormation, or whatever subset of the AWS service ecosystem you care about.

Second, this project is a reference to demonstrate best practices at the intersection of two powerful technologies: GitLab CI and AWS SAM (the Serverless Application Model). Read on for a thorough explanation.

## Quick Start
Run the following command to pull the AWS News SAM project onto your local machine:

`sam init --location git+https://[GitLab project location]`

## SAM Template Walkthrough
*The following section discusses the `sam.yml` file in this repository.*

### What's SAM?

[AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html), at the highest level, is an [open source framework](https://github.com/awslabs/serverless-application-model) for building serverless applications on AWS. You can think of it as an extension to CloudFormation that makes it easier to define and deploy AWS resources -- such as Lambda functions, API Gateway APIs and DynamoDB tables -- commonly used in serverless applications. 

In addition to its templating capabilities, SAM also includes a CLI for testing and deployment, though some of the CLI commands are just aliases to underlying CloudFormation calls. In this project, we used the AWS CloudFormation CLI to build and deploy our SAM application.

### SAM template walkthrough
Our SAM template begins with the following section:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: 'AWS::Serverless-2016-10-31'
Description: >-
  Serverless backend and REST API allowing users to configure personalized weekly updates about AWS products they find relevant.
```

The `AWSTemplateFormatVersion` and `Description` are standard values available in any CloudFormation template. The `Transform` property tells the CloudFormation service to package our special SAM resources as valid CloudFormation before deploying. 

Next we have a `Globals` section:

```yaml
Globals:
  Function:
    Runtime: python2.7
    MemorySize: 128
    Timeout: 30
    Environment:
      Variables:
        LOG_LEVEL: INFO
        REGION: !Ref AWS::Region
        TABLE_NAME: !Ref UserTable
    DeadLetterQueue:
      Type: SNS 
      TargetArn: !Ref DLQNotificationTopic
```

Global SAM values override defaults for any resources where they apply. Here, we've established that all Lambda functions in our template (unless we override globals on a function-specific basis) will have the `python2.7` runtime, a 30-second timeout, and certain environment variables. The `DeadLetterQueue` property specifies an SNS topic to notify in case of function errors.

The template next contains a `Parameters` section and a `Conditions` section. 

```yaml
Parameters:
  DDBThroughput:
    Description: Capacity for the DDB table
    Type: Number
    Default: 1
  Stage:
    Description: A unique identifier for the deployment
    Type: String
    Default: dev
  SenderEmail:
    Description: The email address to send weekly updates from (must be AWS SES-verified)
    Type: String
  VerifiedSenderArn:
    Description: The verified SES ARN (OPTIONAL unless the source account is still in SES sandbox)
    Type: String
  HostedZoneName: 
    Description: The hosted zone to place the API Gateway record in (OPTIONAL)
    Type: String
    Default: ""
  CertificateArn:
    Description: The ACM Certificate ARN (OPTIONAL unless HostedZoneName is specified)
    Type: String

Conditions:
  HasDNS: !Not [!Equals [ !Ref HostedZoneName, "" ]]
```

Again, this is standard CloudFormation syntax. When you deploy the template as a CloudFormation stack, you can pass arguments to these parameters that will be filled in throughout the template.

The `Conditions` section defines a `HasDNS` condition that is true only if the user provides the `HostedZoneName` parameter when deploying the template. We made it optional to set up a custom DNS name for the REST API. If a Route 53 hosted zone is not specified, the API will be created with a default, AWS-specified domain name.

Now we get to the most interesting part: the `Resources` block of the template.

The first resource defined is a Lambda function called `users`:

```yaml
users:
    Type: 'AWS::Serverless::Function'
    Properties:
        CodeUri: ./functions
        Handler: users.lambda_handler
        Description: Handles CRUD operations on users
        Policies:
        - Version: '2012-10-17'
            Statement:
            - Effect: Allow
                Action:
                - dynamodb:GetItem
                - dynamodb:PutItem
                - dynamodb:UpdateItem
                - dynamodb:DeleteItem
                Resource: !Sub arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${UserTable}
        Events:
            Users:
                Type: Api
                Properties:
                Path: /users
                Method: ANY
            Services:
                Type: Api
                Properties:
                Path: /services
                Method: GET
            User:
                Type: Api
                Properties:
                Path: /users/{user}
                Method: ANY
            UserServices:
                Type: Api
                Properties:
                Path: /users/{user}/services
                Method: ANY
```

This `AWS::Serverless::Function` SAM resource looks mostly like a regular AWS CloudFormation Lambda resource, with a few critical differences. Note the `Events` section, which implicitly defines an API Gateway REST API in fron of this function. Each event adds a new route to the API, such as `GET /services` or `ANY /users`.

Note also the inline IAM policy giving access to a DynamoDB table. By default, SAM-created Lambda functions have access to a basic IAM policy allowing them to write CloudWatch logs. We are attaching a second policy adding the DynamoDB permissions.

Another function resource called `fanout` follows:

```yaml
  fanout:
    Type: 'AWS::Serverless::Function'
    Properties:
      Handler: fanout.lambda_handler
      CodeUri: ./functions
      Description: >-
        Reads AWS RSS feed and spawns async Lambda invocations to send user emails
      Timeout: 900
      MemorySize: 512
      Policies:
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - dynamodb:Scan
              Resource: !Sub arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${UserTable}
            - Effect: Allow
              Action:
                - events:Put*
              Resource: '*'
      Events:
        WeeklyEmailRule:
          Type: Schedule
          Properties:
            Schedule: cron(0 8 ? * MON *)
```

In the context of our application, this function will regularly scan DynamoDB and send user information to worker functions for email notification. This function also has an associated event - in this case, a CloudWatch Events Rule running on a weekly schedule. When we package this SAM template, a CloudFormation resource for the rule, and associated permissions for Lambda invocation, will be created automatically.

Note that this function has a different timeout (900 seconds) that overrides the global 30 second timeout.

Our final SAM function is called `emailer`. It takes care of checking the AWS news RSS feed and sending customized email updates to users:

```yaml
    Type: 'AWS::Serverless::Function'
    Properties:
      CodeUri: ./functions
      Handler: emailer.lambda_handler
      Environment:
        Variables:
          AWS_RSS_URL: https://aws.amazon.com/new/feed/
          SENDER_EMAIL: !Ref SenderEmail
          VERIFIED_SENDER_ARN: !Ref VerifiedSenderArn
      Description: >-
        Sends personalized AWS product update emails to a given user
      Policies:
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - ses:Send*
              Resource: '*'
      Events:
        FanoutConsumer:
          Type: CloudWatchEvent
          Properties:
            Pattern:
              source: 
                - "whatsnew.rss.fanout"
```

This function demonstrates yet a third event source integration: with CloudWatch events, in this case to pick up events placed on the CLoudWatch event bus by the fanout function with the source `whatsnew.rss.fanout`. (There are numerous other supported SAM event sources, which you can check out in the [official docs](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md#event-source-types).)

The `CodeUri` property refers to the filesystem location where the function code is stored. (You can check out the Python code for our functions in the `functions` folder of this repository). When we run `aws cloudformation package` on this template, the code in that location will be zipped, uploaded to S3, and the `CodeUri` property in the output CloudFormation template will be replaced with a link to the S3 object.

Note that `CodeUri` is [not currently supported](https://github.com/awslabs/serverless-application-model/blob/master/docs/globals.rst#supported-resources-and-properties) as a global property by the CloudFormation package command, so we have to define it separately in each function configuration.

Next, SAM allows us to minimally define the DynamoDB table we'll be using:

```yaml

  UserTable:
    Type: AWS::Serverless::SimpleTable
    Properties:
      PrimaryKey:
        Name: username
        Type: String
      ProvisionedThroughput:
        ReadCapacityUnits: !Ref DDBThroughput
        WriteCapacityUnits: !Ref DDBThroughput
```

The rest of the template consists of some regular (non-SAM)CloudFormation resources related to the optional DNS name setup, and an output parameter that shows the created API Gateway API name:

```yaml
 DNSRecord:
    Type: AWS::Route53::RecordSet
    Condition: HasDNS
    Properties:
      HostedZoneName: !Sub ${HostedZoneName}.
      Name: !Sub ${Stage}.${HostedZoneName}.
      Type: CNAME
      TTL: '300'
      ResourceRecords:
      - !GetAtt ApiGatewayDomainName.RegionalDomainName
      SetIdentifier: !Ref AWS::Region
      Region: !Ref AWS::Region

  ApiGatewayDomainName:
    Type: "AWS::ApiGateway::DomainName"
    Condition: HasDNS
    Properties:
      RegionalCertificateArn: !Ref CertificateArn
      DomainName: !Sub ${Stage}.${HostedZoneName}
      EndpointConfiguration:
        Types:
          - REGIONAL

  ApiGatewayBasePathMapping:
    Type: AWS::ApiGateway::BasePathMapping
    Condition: HasDNS
    Properties:
      BasePath: ""
      DomainName: !Ref ApiGatewayDomainName
      RestApiId: !Ref ServerlessRestApi
      Stage: !Ref ServerlessRestApiProdStage
  
  DLQNotificationTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: DLQNotifications
      TopicName: !Sub ${AWS::StackName}DLQNotifications

Outputs:
  APIEndpoint:
    Description: URL for API Gateway
    Value: !Sub https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/MyResource/
```

We can mix SAM resources and non-SAM CloudFormation resources freely in the same template, a handy feature.

The interesting thing to note in the above example is that we can refer to implicitly-created SAM resources as though they are defined in the template explicitly. For example, the output `APIEndpoint` is partially constructed from a reference to a resource called `ServerlessRestApi`. That is the API Gateway resource that SAM will produce for us because of the API event defined on our `users` Lambda function.

## GitLab CI template

The attached GitLab CI template has everything you need to set up basic branch-based deployments of this application. Follow the instructions at the top of the file to configure deployments for your environment.