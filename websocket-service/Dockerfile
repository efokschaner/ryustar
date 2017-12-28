FROM node:carbon-alpine

ARG LISTEN_PORT
ENV LISTEN_PORT=${LISTEN_PORT}

WORKDIR /usr/src/app
COPY package.json yarn.lock index.js ./
RUN yarn install --prod && yarn cache clean

ENTRYPOINT node index.js $LISTEN_PORT
