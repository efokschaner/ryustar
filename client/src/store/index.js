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
  userId: getUserId(),
  currentLevel: null,
  hasSetCurrentLevel: false,
  currentVote: null
}

let getters = {
  noLevelInProgress: state => {
    return state.hasSetCurrentLevel && !state.currentLevel
  }
}

let mutations = {
  setCurrentLevel (state, newCurrentLevel) {
    state.currentLevel = newCurrentLevel
    state.hasSetCurrentLevel = true
  },
  setCurrentVote (state, newCurrentVote) {
    state.newCurrentVote = newCurrentVote
  }
}

let pendingCurrentLevelRequest = null
function fetchCurrentLevel ({ commit }) {
  if (pendingCurrentLevelRequest) {
    return pendingCurrentLevelRequest
  }
  async function fetchCurrentLevelInternal () {
    let response = await fetch('/api/level/current')
    let newCurrentLevel = await response.json()
    commit('setCurrentLevel', newCurrentLevel)
    pendingCurrentLevelRequest = null
    return newCurrentLevel
  }
  pendingCurrentLevelRequest = fetchCurrentLevelInternal()
  return pendingCurrentLevelRequest
}

let pendingCurrentVoteRequest = null
function fetchCurrentVote ({ commit, state }) {
  if (pendingCurrentVoteRequest) {
    return pendingCurrentVoteRequest
  }
  async function fetchCurrentVoteInternal () {
    let response = await fetch('/api/vote/' + state.userId)
    let newCurrentVote = await response.json()
    commit('setCurrentVote', newCurrentVote)
    pendingCurrentVoteRequest = null
    return newCurrentVote
  }
  pendingCurrentVoteRequest = fetchCurrentVoteInternal()
  return pendingCurrentVoteRequest
}

let actions = {
  fetchCurrentLevel,
  fetchCurrentVote
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
