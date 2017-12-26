# Ryustar

Built using Google App Engine and Flask and Vue

## Development

### Server
``` bash
pip install -t server/lib -r server/requirements.txt
./dev_server.sh
```

### Client
``` bash
cd client
yarn install
yarn run dev
```

## Deployment
Assuming gcloud (Google Cloud SDK) is installed and configured correctly
``` bash
./deploy.sh
```
There will be some prompts.