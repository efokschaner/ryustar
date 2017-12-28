FROM node:carbon-alpine

ARG LISTEN_PORT

WORKDIR /usr/src/app
COPY package.json yarn.lock index.js ./
RUN yarn install --prod && yarn cache clean
EXPOSE $LISTEN_PORT
CMD node index.js $LISTEN_PORT
