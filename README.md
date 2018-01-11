# RyuStar

The code for https://www.ryustar.io

Built using Google App Engine, Google Container Engine, Flask, Vue.js

## Development

#### Prerequisites
- minikube [See below for general guidance on minikube setup.](#setting-up-minikube)
- jq [(get jq)](https://stedolan.github.io/jq/download/)

### Server
Assuming you have a minikube cluster running, do the following:
- Add entries for:
  - `www.ryustar.invalid`
  - `gke.ryustar.invalid`
  - `gae-admin.ryustar.invalid`

  to your hosts file using your minikube ip, which you can get with `minikube ip`. eg.

      192.168.64.6 www.ryustar.invalid gke.ryustar.invalid gae-admin.ryustar.invalid

  You'll need to update this each time your minikube ip changes (eg. on restart)
- Enable the ingress addon:

      minikube addons enable ingress

- In a separate terminal, mount the app-engine code into minikube vm:

      minikube mount --ip 192.168.64.1 app-engine:/app-engine-src-host
      # Note im using this --ip param to work around https://github.com/kubernetes/minikube/issues/2269


Finally to run services:
``` bash
./dev_server.sh
```
Now try http://www.ryustar.invalid/ and http://gae-admin.ryustar.invalid/ in a browser.

### Client

This runs webpack dev server on your local machine.
Service calls are routed to the `www.ryustar.invalid` domain by the webpack proxy rules.

In principle you could change the proxy to point to the production backend and bypass all the local server setup.

``` bash
cd client
yarn install
yarn run dev
```

## Deployment
#### Prerequisites
- `gcloud` (Google Cloud SDK) is installed and configured correctly
- `kubectl` is installed. You can get it via `gcloud components install kubectl`
- `gcloud container clusters get-credentials ryustar-cluster-0 --zone us-central1-a`

``` bash
./deploy.sh
```

## Appendix

### Updating app-engine vendored pip dependencies
Pip does not support freezing a vendored dir of libs which makes maintaining the requirements.txt a pain
One workaround is to create a virtualenv just for re-jigger-ing dependencies and then freezing it,
then switching back to installing into the vendored dir. eg.
```bash
pyenv virtualenv venv
pyenv activate venv
pip install -r requirements.txt
pip install google-api-python-client
pip freeze > requirements.txt
pyenv deactivate
pyenv uninstall venv
```

### Setting up minikube
You'll need minikube to run a local container cluster.

Installing minikube: https://github.com/kubernetes/minikube and https://kubernetes.io/docs/getting-started-guides/minikube/

minikube may need hyperkit or some other driver: https://github.com/kubernetes/minikube/blob/master/docs/drivers.md#hyperkit-driver

If using non-default (virtualbox) driver:

    # replace "hyperkit" with your driver
    minikube config set vm-driver hyperkit

You'll also need Docker for your platform: https://store.docker.com/

Get minikube up and running to use the rest of this readme:

    minikube start

### GKE notes
Manually creating nodepool with necessary pubsub auth scope:

    gcloud container node-pools create node-pool-0 --cluster=ryustar-cluster-0 --disk-size=10 --enable-autoupgrade --machine-type=f1-micro --num-nodes=3 --zone=us-central1-a --scopes=gke-default,pubsub

Before any other clusterrole configs can be made:

    kubectl create clusterrolebinding CHOOSE_A_FILENAME-cluster-admin-binding --clusterrole=cluster-admin --user=<YOUR_USERNAME>

Install latest dashboard:
- Disable built in kube dash in GCP Console
- kubectl create -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/recommended/kubernetes-dashboard.yaml

Production dashboard:

    kubectl proxy

http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/

Get token from access-token in ~/.kube/config

#### Ingress creation woes
Try creating ingress WITHOUT these annotation first otherwise it gets stuck "creating ingress"

    # kubernetes.io/ingress.allow-http: "false"
    # kubernetes.io/tls-acme: "true"

Might need to create a fake TLS cert to allow bootstrapping kube-lego and its self-check:

    openssl req -x509 -nodes -days 1 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=gke.ryustar.io/O=gke.ryustar.io"
    kubectl create secret tls gke-ryustar-io-certificate --key tls.key --cert tls.crt

In fact maybe this second "fix" is what was breaking the initial deploy...

Manual updates to lb for websockets because gce ingress does not support this configuration from kubernetes:
Access the backend services in the "advanced menu" of Load Balancing section of the web console
Set timeout to 1h (3600s)
