let http = require('http')
let os = require('os')

let PubSub = require('@google-cloud/pubsub')
let uuidv4 = require('uuid/v4')
let WebSocketServer = require('websocket').server

let logger = require('./logger')

process.on('unhandledRejection', error => {
  throw error
})

function createTopicSubscription (topicName, subscriptionName) {
  const pubsub = PubSub()
  const topic = pubsub.topic(topicName)
  return topic.createSubscription(subscriptionName, {
    messageRetentionDuration: 10 * 60 // seconds
  }).then((results) => {
    const subscription = results[0]
    logger.info(`Subscription ${subscription.name} created.`)
    return subscription
  })
}

class WebSocketBroadCastServer {
  constructor () {
    this.httpServer = http.createServer(function (request, response) {
      // Default readycheck from GCP goes to / and expects 200
      response.writeHead(200)
      response.end()
    })
    this.wsServer = new WebSocketServer({
      httpServer: this.httpServer,
      autoAcceptConnections: false,
      keepaliveInterval: 50000
    })
    this.wsServer.on('request', this._handleWebsocketUpgradeRequest.bind(this))
  }

  listen (serverPort) {
    return new Promise((resolve, reject) => {
      this.httpServer.listen(serverPort, () => {
        let address = this.httpServer.address()
        logger.info('HTTP server is listening', {address})
        resolve(address)
      })
      this.httpServer.on('error', (err) => {
        reject(err)
      })
    })
  }

  broadcast (message) {
    return this.wsServer.broadcastUTF(message)
  }

  shutDown () {
    this.wsServer.shutDown()
    this.httpServer.close()
  }

  _handleWebsocketUpgradeRequest (request) {
    if (!this._originIsAllowed(request.origin)) {
      request.reject()
      logger.info(`Connection from origin ${request.origin} rejected.`)
      return
    }
    let wsConnection = request.accept(undefined, request.origin)
    wsConnection.on('message', function (message) {
      // For now we're not expecting any client-to-server messages
      // If we receive one, assume the client is misbehaving and close the connection
      wsConnection.close()
    })

    wsConnection.on('close', function (reasonCode, description) {
      // logger.info(`WebSocket client ${wsConnection.remoteAddress} disconnected.`)
    })
  }

  _originIsAllowed (origin) {
    // put logic here to detect whether the specified origin is allowed.
    // I see no reason for this public s2c-only endpoint to have any origin restrictions.
    return true
  }
}

async function main () {
  logger.info('websocket-service starting', {env: process.env})
  let listenPortString = process.argv[2] || process.env.LISTEN_PORT || '9090'
  let listenPort = parseInt(listenPortString)
  let server = new WebSocketBroadCastServer()
  await server.listen(listenPort)
  // Subscription ids must start with a letter and have other constraints
  // see https://github.com/googleapis/googleapis/blob/f0f1588a68ad2c58ea2e9352b083e04a20859d3c/google/pubsub/v1/pubsub.proto#L406
  let subscriptionId = `s-${os.hostname()}-${uuidv4()}`
  let subscription = await createTopicSubscription('ryustar-io-endpoints-topic', subscriptionId)

  async function handleShutdown () {
    // Here we try to gracefully shutdown. Including deleting our dynamic subscription
    // from gcloud pubsub. Of course this is not guaranteed to work and so we should implement a
    // cron to clean up those subscriptions somehow.
    logger.info('Received signal. Shutting down.')
    server.shutDown()
    await subscription.close()
    await subscription.delete()
  }

  process.on('SIGINT', handleShutdown)
  process.on('SIGTERM', handleShutdown)

  subscription.on('error', function (err) {
    logger.error(`subscriptions error: ${err}`)
  })

  function onMessage (message) {
    message.ack()
    let dataString = Buffer.from(message.data, 'base64').toString()
    server.broadcast(dataString)
  }

  subscription.on('message', onMessage)

  logger.info('websocket-service is fully initialised')
}

if (require.main === module) {
  main()
}
