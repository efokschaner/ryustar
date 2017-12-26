#!/bin/bash
set -o nounset
set -o errexit

# Deletes all files and folders that match the .gitignore (uncommited stuff that is tracked is let alone)
git clean -f -d -X
pushd client
yarn install
yarn run build
popd
pushd server
pip install -t lib/ -r requirements.txt
popd
gcloud app deploy server/app.yaml