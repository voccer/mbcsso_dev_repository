# MBC

[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![jp](https://img.shields.io/badge/lang-jp-yellow.svg)](README_ja.md)

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders.

- docs - Documents for application
- infra - Folder contains infra code
- src - Code for the application's Lambda function.
- test - everything test

## Getting Started

### Prerequisites

- git
- python 3.9
- pip
- virtualenv
- vscode
- docker [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
- SAM CLI [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

## Deploy the

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

To build and deploy your application for the first time, run the following in your shell:

```bash
$ cd infra/sam_mbc
$ sam build -t template.yaml
$ sam deploy --profile <specific profile from your credential file to get AWS credentials> -g
```

The first command will build a docker image from a Dockerfile and then copy the source of your application inside the Docker image. The second command will package and deploy your application to AWS, with a series of prompts:

- **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching your project name.
- **AWS Region**: The AWS region you want to deploy your app to.
- **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
- **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this example, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
- **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to your application.

You can find your API Gateway Endpoint URL in the output values displayed after deployment.

## Add a resource to your application

The application template uses AWS Serverless Application Model (AWS SAM) to define application resources. AWS SAM is an extension of AWS CloudFormation with a simpler syntax for configuring common serverless application resources such as functions, triggers, and APIs. For resources not included in [the SAM specification](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md), you can use standard [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html) resource types.

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.

## Codebuild/Codepipeline
The application that demonstrates continuous integration with AWS CodeBuild/Codepipeline, and GitHub
- About [Codebuild](https://aws.amazon.com/codebuild/)
- About [Codepipeline](https://aws.amazon.com/codepipeline/)

### CI Tooling (Buildspecs)
The buildspecs folder contains the following buildspec files for use with AWS CodeBuild

src/buildspec.yaml: Build the docker images
