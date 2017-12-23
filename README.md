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
``` bash
pushd server
pip install -t lib -r requirements.txt
popd
pushd client
yarn run build
popd
# ??????
# PROFIT
``` 
