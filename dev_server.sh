#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

k8s/build.sh

pip install -t app-engine/server/lib -r app-engine/server/requirements.txt

WEBSOCKET_CONTAINER_IMAGE=$(jq --raw-output '(.base + .minikube)."websocket-service-container-image"' global-config.json)
WEBSOCKET_CONTAINER_LISTEN_PORT=$(jq --raw-output '(.base + .minikube)."websocket-service-container-listen-port"' global-config.json)
eval $(minikube docker-env)
docker build -t ${WEBSOCKET_CONTAINER_IMAGE} websocket-service --build-arg LISTEN_PORT=${WEBSOCKET_CONTAINER_LISTEN_PORT}

kubectl apply -f k8s/dist/minikube
