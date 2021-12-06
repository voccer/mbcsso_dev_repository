#! /bin/bash
MY_FUNC=mbcsso_dev_ProcessSQSFunction
IMAGE_URI=$(aws lambda get-function --function-name $MY_FUNC | jq -r '.Code.ImageUri')

# Set comma as delimiter
IFS='/'

read -a strarr <<< "$IMAGE_URI"
CLOUD_URL=${strarr[0]}
REPO_TAG_NAME=${strarr[1]}/${strarr[2]}

IFS=':'
read -a strarr <<< "$REPO_TAG_NAME"
REPO_NAME=${strarr[0]}
CURRENT_TAG_NAME=${strarr[1]}

LATEST_TAG_NAME="latest"

TAG_NAME="1"

echo "CLOUD_URL: $CLOUD_URL"
echo "REPO_NAME: $REPO_NAME"
echo "TAG_NAME: $TAG_NAME"

aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $CLOUD_URL

docker build -t $CLOUD_URL/$REPO_NAME:$CURRENT_TAG_NAME .
docker tag $CLOUD_URL/$REPO_NAME:$CURRENT_TAG_NAME $CLOUD_URL/$REPO_NAME:$TAG_NAME

if [ "$CURRENT_TAG_NAME" != "$LATEST_TAG_NAME" ]; then
  docker tag $CLOUD_URL/$REPO_NAME:$CURRENT_TAG_NAME $CLOUD_URL/$REPO_NAME:$LATEST_TAG_NAME
fi
docker push $CLOUD_URL/$REPO_NAME:$LATEST_TAG_NAME
docker push $CLOUD_URL/$REPO_NAME:$TAG_NAME

aws lambda update-function-code --function-name $MY_FUNC --image-uri "${CLOUD_URL}/${REPO_NAME}:${LATEST_TAG_NAME}" >> /dev/null