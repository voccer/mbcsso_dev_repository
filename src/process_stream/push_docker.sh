#! /bin/bash
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 465316005105.dkr.ecr.ap-northeast-1.amazonaws.com
docker build -t  samdbb5da54c1/processstreamddbfunction63e41201repo:processstreamddbfunction-03572dcb4392-python3.9-v1 .
docker tag samdbb5da54c1/processstreamddbfunction63e41201repo:processstreamddbfunction-03572dcb4392-python3.9-v1  465316005105.dkr.ecr.ap-northeast-1.amazonaws.com/samdbb5da54c1/processstreamddbfunction63e41201repo:processstreamddbfunction-03572dcb4392-python3.9-v1
docker push 465316005105.dkr.ecr.ap-northeast-1.amazonaws.com/samdbb5da54c1/processstreamddbfunction63e41201repo:processstreamddbfunction-03572dcb4392-python3.9-v1
MY_FUNC=mbcsso_dev_ProcessStreamFunction
aws lambda update-function-code --function-name $MY_FUNC --image-uri $(aws lambda get-function --function-name $MY_FUNC | jq -r '.Code.ImageUri')