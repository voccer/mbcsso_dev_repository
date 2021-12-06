## Get Services

Show all AWS products and services currently supported by the API

**Path** : `/services`

**Method** : `GET`

##### Success Response

**Code** : `200 OK`

**Example**

`curl https://[api-endpoint.com]/services`

```json
["ec2", "s3", "lambda", "ebs", "rds", "sagemaker", "iot", "fargate", "route-53", "workdocs", "sumerian", "gamelift", "batch", "elastic-beanstalk", "cloudformation", "cloudwatch", "cloudfront", "cloudtrail", "config", "step-functions", "swf", "ses", "sns", "sqs", "ses", "vpc", "sam", "pinpoint", "x-ray", "snowball"]
```

## Post User

Create a new user in the API

**Path** : `/users`

**Method** : `POST`

#### Success Response

**Code** : `200 OK`

**Example**

`curl -XPOST https://[api-endpoint.com]/users -d '{"username":"testuser","email":"example@test.com"}`

`"Successfully saved new user"`

## Put User

Update properties for an existing user. Currently `email` is the only supported property.

**Path** : `/users/{username}`

**Method** : `PUT`

#### Success Response

**Code** : `200 OK`

**Example**

`curl -XPUT https://[api-endpoint.com]/users/testuser -d '{"email":"example2@test.com"}`

`"Successfully updated user"`

## Get User

Get properties for an existing user

**Path** : `/users/{username}`

**Method** : `GET`

#### Success Response

**Code** : `200 OK`

**Example**

`curl https://[api-endpoint.com]/users/testuser`

```json
{"username":"testuser","email":"example@test.com"}
```

## Put User Services

Add or remove services for an existing user

**Path** : `/users/{username}/services`

**Method** : `PUT`

#### Success Response

**Code** : `200 OK`

**Example: Add new services**

`curl -XPUT https://[api-endpoint.com]/users/testuser/services -d '{"services":["ec2","cloudformation"], "action":"ADD"'`

`Successfully updated user services`

**Example: Remove services**

`curl -XPUT https://[api-endpoint.com]/users/testuser/services -d '{"services":["cloudformation"], "action":"REMOVE"'`

`Successfully updated user services`

## Get User Services

Get services for an existing user

**Path** : `/users/{username}/services`

**Method** : `GET`

#### Success Response

**Code** : `200 OK`

**Example**

`curl https://[api-endpoint.com]/users/testuser/services`

```json
["ec2","cloudformation"]
```

## Delete User

Remove a user for the system

**Path** : `/users/{username}`

**Method** : `DELETE`

#### Success Response

**Code** : `200 OK`

**Example**

`curl https://[api-endpoint.com]/users/testuser`

`"Successfully deleted user"`