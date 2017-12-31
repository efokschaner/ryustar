let http = require('http')

let PubSub = require('@google-cloud/pubsub')
let uuidv4 = require('uuid/v4')
let WebSocketServer = require('websocket').server

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
    console.log(`Subscription ${subscription.name} created.`)
    return subscription
  })
}

class WebSocketBroadCastServer {
  constructor () {
    this.httpServer = http.createServer(function (request, response) {
      response.writeHead(404)
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
        let address = this.httpServer.address();
        console.log('HTTP server is listening on ', address);
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
    this.httpServer.shutDown()
  }

  _handleWebsocketUpgradeRequest (request) {
    if (!this._originIsAllowed(request.origin)) {
      request.reject()
      console.log('Connection from origin ' + request.origin + ' rejected.')
      return
    }
    let wsConnection = request.accept(undefined, request.origin)
    wsConnection.on('message', function (message) {
      // For now we're not expecting any client-to-server messages
      // If we receive one, assume the client is misbehaving and close the connection
      wsConnection.clos()
    })

    wsConnection.on('close', function (reasonCode, description) {
      console.log('WebSocket client ' + wsConnection.remoteAddress + ' disconnected.');
    })
  }

  _originIsAllowed (origin) {
    // put logic here to detect whether the specified origin is allowed.
    return true
  }
}

async function main () {
  let listenPortString = process.argv[2] || process.env.LISTEN_PORT || '9090'
  let listenPort = parseInt(listenPortString)
  let server = new WebSocketBroadCastServer()
  await server.listen(listenPort)
  let subscriptionId = uuidv4()
  let subscription = await createTopicSubscription('level-updates-topic', subscriptionId)

  async function handleShutdown (signal) {
    // Here we try to gracefully shutdown. Including deleting our dynamic subscription
    // from gcloud pubsub. Of course this is not guaranteed to work and so we should implement a
    // cron to clean up those subscriptions somehow.
    console.log(`Received ${signal}. Shutting down.`)
    server.shutDown()
    await subscription.close()
    await subscription.delete()
  }

  process.on('SIGINT', handleShutdown)
  process.on('SIGTERM', handleShutdown)

  subscription.on('error', function (err) {
    console.error('subscriptions error:', err)
  })

  function onMessage (message) {
    message.ack()
    let dataString = Buffer.from(message.data, 'base64').toString()
    server.broadcast(dataString)
  }

  subscription.on('message', onMessage)

  console.info('websocket-service is fully initialised')
}

if (require.main === module) {
  main()
}
