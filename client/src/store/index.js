import Vue from 'vue'
import Vuex from 'vuex'
import createLogger from 'vuex/dist/logger'

Vue.use(Vuex)

const debug = process.env.NODE_ENV !== 'production'

function uuidv4 () {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    let r = Math.random() * 16 | 0
    let v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

function getUserId () {
  let prior = window.localStorage.getItem('user_id')
  if (prior) {
    return prior
  }
  let newId = uuidv4()
  window.localStorage.setItem('user_id', newId)
  return newId
}

let state = {
  user_id: getUserId(),
  current_level: null,
  current_vote: null
}

let getters = {
  cartProducts: state => {
    return state.cart.added.map(({ id, quantity }) => {
      const product = state.products.all.find(p => p.id === id)
      return {
        title: product.title,
        price: product.price,
        quantity
      }
    })
  }
}

let mutations = {
}

let actions = {
  addToCart: ({ commit }, product) => {
    if (product.inventory > 0) {
      commit('types.ADD_TO_CART', {
        id: product.id
      })
    }
  }
}

let modules = {}

export default new Vuex.Store({
  actions,
  getters,
  modules,
  mutations,
  state,
  strict: debug,
  plugins: debug ? [createLogger()] : []
})
