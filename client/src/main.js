// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store'
import * as ws from './webscoket'

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  template: '<App/>',
  components: { App }
})

function onNewLevelData (newCurrentLevel) {
  store.commit('setCurrentLevel', newCurrentLevel)
}

ws.start('ws://ws.ryustar.invalid/', onNewLevelData)
