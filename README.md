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
  - `ws.ryustar.invalid`
  - `gae-admin.ryustar.invalid`

  to your hosts file using your minikube ip, which you can get with `minikube ip`. eg.

      192.168.64.6 www.ryustar.invalid ws.ryustar.invalid gae-admin.ryustar.invalid

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
``` bash
./deploy.sh
```
There will be some prompts.

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
