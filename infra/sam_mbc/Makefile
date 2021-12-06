api:
	sam build -t template_api.yaml && sam deploy --config-file samconfig_api.toml

dynamodb:
	sam build -t template_db.yaml && sam deploy --config-file samconfig_db.toml

sns-to-queue:
	sam build -t template_sns.yaml && sam deploy --config-file samconfig_sns.toml

sso:
	sam build -t template.yaml && sam deploy --config-file samconfig.toml

api-g:
	sam build -t template_api.yaml && sam deploy -g --config-file samconfig_api.toml

dynamodb-g:
	sam build -t template_db.yaml && sam deploy -g --config-file samconfig_db.toml

sns-to-queue-g:
	sam build -t template_sns.yaml && sam deploy -g --config-file samconfig_sns.toml

sso-g:
	sam build -t template.yaml && sam deploy -g --config-file samconfig.toml
