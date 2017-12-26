# Ryustar

Built using Google App Engine and Flask and Vue

## Development

### Server
``` bash
cd server
pip install -t lib -r requirements.txt
dev_appserver.py app.yaml
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