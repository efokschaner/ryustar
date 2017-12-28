FROM google/cloud-sdk:latest

# TODO mount app-engine dir
# WORKDIR /usr/src/app

RUN pip install -t server/lib -r server/requirements.txt
EXPOSE 8080
CMD dev_appserver.py dispatch.yaml server/app.yaml www-redirect-service/app.yaml
