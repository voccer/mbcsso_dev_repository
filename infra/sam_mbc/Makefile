dynamodb:
	sam build -t template_db.yaml && sam deploy --config-file samconfig_db.toml

sso:
	sam build -t template.yaml && sam deploy --config-file samconfig.toml

dynamodb-g:
	sam build -t template_db.yaml && sam deploy -g --config-file samconfig_db.toml

sso-g:
	sam build -t template.yaml && sam deploy -g --config-file samconfig.toml
