FROM node:carbon-alpine

WORKDIR /usr/src/app
COPY package.json yarn.lock index.js ./
RUN yarn install --prod && yarn cache clean
EXPOSE 9090
CMD node index.js 9090
