#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

# Deletes all files and folders that match the .gitignore (uncommited stuff that is tracked is let alone)
git clean -f -d -X

# Builds
k8s/build.sh

pushd client
yarn install
yarn run build
popd

pip install --target app-engine/server/lib -r app-engine/server/requirements.txt

WEBSOCKET_CONTAINER_IMAGE=$(jq --raw-output '(.base + .gcloud)."websocket-service-container-image"' global-config.json)
docker build -t ${WEBSOCKET_CONTAINER_IMAGE} websocket-service

# Deploys

gcloud docker -- push ${WEBSOCKET_CONTAINER_IMAGE}

gcloud beta pubsub topics create level-updates-topic || echo "Creating topic that already exists is expected to fail"

gcloud app deploy --quiet app-engine/server/queue.yaml

gcloud app deploy --quiet --stop-previous-version app-engine/server/app.yaml app-engine/www-redirect-service/app.yaml

gcloud app deploy --quiet app-engine/dispatch.yaml

kubectl apply --context="gke_studious-osprey-189923_us-central1-a_ryustar-cluster-0" -f k8s/dist/gcloud
