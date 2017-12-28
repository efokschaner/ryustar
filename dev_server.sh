#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

k8s/build.sh

WEBSOCKET_CONTAINER_IMAGE=$(jq '(.base + .minikube)."websocket-service-container-image"' global-config.json)
WEBSOCKET_CONTAINER_LISTEN_PORT=$(jq '(.base + .minikube)."websocket-service-container-listen-port"' global-config.json)

pushd websocket-service
eval $(minikube docker-env)
docker build -t ${WEBSOCKET_CONTAINER_IMAGE} . --build-arg LISTEN_PORT=${WEBSOCKET_CONTAINER_LISTEN_PORT}
popd

kubectl apply -f k8s/dist/minikube
