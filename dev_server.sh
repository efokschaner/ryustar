#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

k8s/build.sh

pip install --target app-engine/server/lib -r app-engine/server/requirements.txt

WEBSOCKET_CONTAINER_IMAGE=$(jq --raw-output '(.base + .minikube)."websocket-service-container-image"' global-config.json)
eval $(minikube docker-env)
docker build -t ${WEBSOCKET_CONTAINER_IMAGE} websocket-service

docker build -t dev-appserver-proxy:local-dev dev-appserver-proxy

kubectl apply --context="minikube" -f k8s/dist/minikube
