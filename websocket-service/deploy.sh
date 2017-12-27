#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

cd "$(dirname "$0")"

# needed for mustache
yarn install

PROJECT_ID="$(gcloud config get-value project -q)"
CONTAINER_IMAGE="gcr.io/${PROJECT_ID}/websocket-service:latest"

docker build -t ${CONTAINER_IMAGE} .
gcloud docker -- push ${CONTAINER_IMAGE}

rm -rf k8s/GKE
mkdir k8s/GKE
for file in k8s/*.mustache; do
  IN_FILENAME="${file#k8s/}"
  OUT_FILENAME="${IN_FILENAME%.mustache}"
  yarn run mustache <(echo "{ \"CONTAINER_IMAGE\": \"${CONTAINER_IMAGE}\" }") "$file" "k8s/GKE/${OUT_FILENAME}"
done

kubectl apply -f k8s/GKE/
