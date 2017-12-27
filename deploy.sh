#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

# Deletes all files and folders that match the .gitignore (uncommited stuff that is tracked is let alone)
git clean -f -d -X

# Builds
pushd client
yarn install
yarn run build
popd

pip install -t server/lib -r server/requirements.txt

# Deploys (technically should move build steps out of websocket-service/deploy.sh)
websocket-service/deploy.sh
gcloud app deploy server/app.yaml
gcloud app deploy www-redirect-service/app.yaml
gcloud app deploy dispatch.yaml
