import * as ReconnectingWebSocket from 'reconnecting-websocket'

function createReconnectingWebSocket (url) {
  let reconnectingWebSocketConfig = {
    maxReconnectionDelay: 90000,
    minReconnectionDelay: 5000,
    reconnectionDelayGrowFactor: 1.3,
    connectionTimeout: 20000,
    maxRetries: Infinity,
    debug: false
  }
  return new ReconnectingWebSocket(url, [], reconnectingWebSocketConfig)
}

let websocket = null

export function initWebsocketForStore (store) {
  store.watch(
    function (state) {
      return state.config ? state.config.websocket_url : null
    },
    function (websocketUrl) {
      if (websocket) {
        websocket.close()
        websocket = null
      }
      if (websocketUrl) {
        websocket = createReconnectingWebSocket(websocketUrl)
        websocket.onmessage = function (evt) {
          let { url, body } = JSON.parse(evt.data)
          // To Do make this data-driven and shard with vuex store CRUD
          if (url === '/api/level/current') {
            store.commit('setCurrentLevel', JSON.parse(body))
          } else if (url === '/api/config') {
            // Add jitter to the commit of config updates to reduce stampeding
            setTimeout(
              () => {
                store.commit('setConfig', JSON.parse(body))
              },
              Math.random() * 30 * 1000
            )
          } else {
            throw new Error(`Unrecognised url received from websocket: ${url} , evt: ${evt.data}`)
          }
        }
        websocket.onopen = function () {
          store.commit('setWebSocketHasError', false)
        }
        websocket.onclose = function (evt) {
          console.error(`WebSocket connection to '${websocket.url}' closed. Reason: '${evt.reason}'. Code: ${evt.code}`)
          store.commit('setWebSocketHasError', true)
        }
      }
    }
  )
}
