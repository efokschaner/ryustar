#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

cd "$(dirname "$0")"

# needed for mustache
yarn install

CONTAINER_IMAGE="websocket-service:latest"

eval $(minikube docker-env)
docker build -t ${CONTAINER_IMAGE} .

rm -rf k8s/minikube
mkdir k8s/minikube
for file in k8s/*.mustache; do
  IN_FILENAME="${file#k8s/}"
  OUT_FILENAME="${IN_FILENAME%.mustache}"
  yarn run mustache <(echo "{ \"CONTAINER_IMAGE\": \"${CONTAINER_IMAGE}\" }") "$file" "k8s/minikube/${OUT_FILENAME}"
done

kubectl apply -f k8s/minikube/
