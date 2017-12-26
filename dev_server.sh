#!/bin/bash
set -o nounset
set -o errexit

dev_appserver.py dispatch.yaml server/app.yaml www-redirect-service/app.yaml