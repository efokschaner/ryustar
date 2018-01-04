// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store'

import * as ReconnectingWebSocket from 'reconnecting-websocket'
import { fetchJson } from './fetch.js'

function createReconnectingWebSocket (url) {
  let reconnectingWebSocketConfig = {
    maxReconnectionDelay: 90000,
    minReconnectionDelay: 5000,
    reconnectionDelayGrowFactor: 1.3,
    connectionTimeout: 10000,
    maxRetries: Infinity,
    debug: false
  }
  return new ReconnectingWebSocket(url, [], reconnectingWebSocketConfig)
}

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App }
})

async function initWithConfig () {
  let config = await fetchJson('/api/config')

  let websocket = createReconnectingWebSocket(config.websocket_url)

  websocket.onmessage = function (evt) {
    store.commit('setCurrentLevel', JSON.parse(evt.data))
  }

  websocket.onopen = function () {
    store.commit('setWebSocketHasError', false)
  }

  websocket.onclose = function (evt) {
    console.error(`WebSocket connection to ${websocket.url} closed. Reason: ${evt.reason}. Code: ${evt.code}`)
    store.commit('setWebSocketHasError', true)
  }
}

initWithConfig()
