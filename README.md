# Ryustar

Built using Google App Engine and Flask and Vue

## Development

### Server

You'll need minikube to run local containers: https://github.com/kubernetes/minikube and https://kubernetes.io/docs/getting-started-guides/minikube/

minikube may need hyperkit or some other driver: https://github.com/kubernetes/minikube/blob/master/docs/drivers.md#hyperkit-driver

If using non-default (virtualbox) driver:

    # replace "hyperkit" with your driver
    minikube config set vm-driver hyperkit

You'll also need Docker for your platform: https://store.docker.com/

You must have minikube already running:

    minikube start

And you must enable the ingress addon:

    minikube addons enable ingress

`pip install` only needed on first run or if you change deps

    pip install -t server/lib -r server/requirements.txt

Finally to run services:
``` bash
./dev_server.sh
```

### Client
``` bash
cd client
yarn install
yarn run dev
```

## Deployment
Assuming `gcloud` (Google Cloud SDK) is installed and configured correctly
If you don't have gcloud kubectl: `gcloud components install kubectl`
``` bash
./deploy.sh
```
There will be some prompts.
