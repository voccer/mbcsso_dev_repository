printf "input docker repo: "
read DOCKER_REPO

printf "input latest docker tag(default is latest): "
read LATEST_DOCKER_TAG
if [ -z "$LATEST_DOCKER_TAG" ]; then
  LATEST_DOCKER_TAG=latest
fi

printf "input your aws profile(default is default): "
read AWS_PROFILE
if [ -z "$AWS_PROFILE" ]; then
  AWS_PROFILE=default
fi

echo "profile is $AWS_PROFILE"
DOCKER_TAG=$DOCKER_REPO:$LATEST_DOCKER_TAG

echo "docker tag $DOCKER_TAG"
docker build -t $DOCKER_TAG ./docker

# login
ECR_URI=$(echo ${DOCKER_REPO} | cut -d "/" -f 1)
echo "ECR_URI is $ECR_URI"

aws ecr get-login-password  | docker login --username AWS --password-stdin ${ECR_URI}

docker push $DOCKER_TAG