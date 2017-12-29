FROM node:carbon-alpine

WORKDIR /usr/src/app
COPY package.json yarn.lock index.js ./
RUN yarn install --prod && yarn cache clean

# Use json form so that node is pid 1 and can handle sigterm
ENTRYPOINT ["node", "index.js"]
