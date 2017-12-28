#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

cd "$(dirname "$0")"

# needed for mustache
yarn install



rm -rf k8s/gcloud
mkdir k8s/gcloud
for file in k8s/*.mustache; do
  IN_FILENAME="${file#k8s/}"
  OUT_FILENAME="${IN_FILENAME%.mustache}"
  yarn run mustache <(echo "{ \"CONTAINER_IMAGE\": \"${CONTAINER_IMAGE}\" }") "$file" "k8s/gcloud/${OUT_FILENAME}"
done

kubectl apply -f k8s/gcloud/
