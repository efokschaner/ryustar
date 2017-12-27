#!/bin/bash
set -o nounset
set -o errexit
set -o verbose

websocket-service/run_in_minikube.sh
dev_appserver.py dispatch.yaml server/app.yaml www-redirect-service/app.yaml
