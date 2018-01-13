// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import Toasted from 'vue-toasted'

import App from './App'
import router from './router'
import store from './store'

Vue.use(Toasted)

Vue.toasted.register('genericError',
  (payload) => {
    if (!payload.message) {
      return 'Something went wrong. Perhaps try again in a moment.'
    }
    return payload.message
  },
  {
    type: 'error',
    icon: 'error',
    position: 'bottom-center',
    duration: 15000,
    theme: 'outline',
    action: {
      text: 'Dismiss',
      onClick (e, toastObject) {
        toastObject.goAway(0)
      }
    }
  }
)

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App }
})

store.watch(
  function (state) {
    return state.websocketHasError
  },
  function (websocketHasError) {
    if (websocketHasError) {
      Vue.toasted.global.genericError(
        { message: 'The connection to the server is failing. The information on the page may be stale.' }
      )
    }
  }
)
