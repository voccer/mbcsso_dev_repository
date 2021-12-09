
# !/bin/bash
cd infra/sam_mbc
sam build -t template_db.yaml

printf "Enter profile name [required]:"
read PROFILE
if [ -z "$PROFILE" ]
then echo "Profile name is required"
    exit 1
fi

sam deploy --profile $PROFILE -g

printf "Enter system name [default: mbcsso]:"
read Name
printf "Enter env [default: dev]:"
read Env

if [ -z "$Name" ]
then Name="mbcsso"
fi

if [ -z "$Env" ]
then Env="dev"
fi

TABLE_CONFIG_NAME="${Name}_${Env}_Config"

#create item Config table
aws dynamodb put-item \
    --table-name $TABLE_CONFIG_NAME \
    --item '{ 
        "system_id": {"S": "1"}, 
        "tenant_id": {"S": "1"} , 
        "admin": {"S": "dev-admin"},
        "client_id": {"S": "sso-lambda"},
        "keycloak_url": {"S": "https://dev.sso-service.com"},
        "keycloak_realm": {"S": "devs"},
        "password": {"S": "AQICAHidx/6BTLp0wg1UBw7cjvQdfoPXHCN/qdoTrXLhVs4FTQEzZ/Ph2Ja6ruv+B8QbA6tgAAAAejB4BgkqhkiG9w0BBwagazBpAgEAMGQGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMzJPhJTLofbOfpzIAAgEQgDfgOmzG8ze37QwCfxQnTMJbFy8r908C+dlLjoEWZNPUo3I7kxG7tCfdswpUMdS+yCDA3hzeSvK/"}
      }' \
    --return-consumed-capacity TOTAL