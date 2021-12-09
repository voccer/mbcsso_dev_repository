ACCOUNT_ID=465316005105
SYSTEM_NAME=mbcsso
ENV=dev
LATEST_TAG="latest"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
FUNCTION_NAME=${SYSTEM_NAME}_${ENV}_ProcessSQSFunction
FUNCTION_SRC_DIR="."


# login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

IMAGE_URI=$(aws lambda get-function --function-name $FUNCTION_NAME | jq -r '.Code.ImageUri')

REPO_NAME=$(echo ${IMAGE_URI} | cut -d "/" -f 2)/$(echo ${IMAGE_URI} | cut -d "/" -f 3)

COMMIT_HASH=$(echo "923hjh")
IMAGE_TAG=${COMMIT_HASH:=latest}
echo $IMAGE_TAG

docker build -t $ECR_URI/$REPO_NAME:$LATEST_TAG $FUNCTION_SRC_DIR
docker tag $ECR_URI/$REPO_NAME:$LATEST_TAG $ECR_URI/$REPO_NAME:$IMAGE_TAG

docker push $ECR_URI/$REPO_NAME:$IMAGE_TAG
docker push $ECR_URI/$REPO_NAME:$LATEST_TAG

aws lambda update-function-code --function-name $FUNCTION_NAME --image-uri $ECR_URI/$REPO_NAME:$LATEST_TAG
