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

async function fetchJson (url, fetchOptions) {
  let response = await fetch(url, fetchOptions)
  if (!response.ok) {
    let errorText = await response.text()
    throw new Error(`HTTP ${response.status} from ${response.url} : ${errorText}`)
  }
  return response.json()
}

let state = {
  currentLevel: null,
  hasSetCurrentLevel: false,
  currentVote: null,
  websocketHasError: false
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
  applyPredicitonToCurrentLevel (state, {oldChoice, newChoice}) {
    state.currentLevel[newChoice + '_votes_count'] += 1
    let oldKey = oldChoice + '_votes_count'
    if (oldKey in state.currentLevel) {
      state.currentLevel[oldKey] -= 1
    }
  },
  setCurrentVote (state, newCurrentVote) {
    state.currentVote = newCurrentVote
  },
  setWebSocketHasError (state, newWebSocketHasError) {
    state.websocketHasError = newWebSocketHasError
  }
}

let pendingCurrentLevelRequest = null
function fetchCurrentLevel ({ commit }) {
  if (pendingCurrentLevelRequest) {
    return pendingCurrentLevelRequest
  }
  async function fetchCurrentLevelInternal () {
    let newCurrentLevel = await fetchJson('/api/level/current')
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
    let newCurrentVote = await fetchJson('/api/vote/' + getUserId())
    commit('setCurrentVote', newCurrentVote)
    pendingCurrentVoteRequest = null
    return newCurrentVote
  }
  pendingCurrentVoteRequest = fetchCurrentVoteInternal()
  return pendingCurrentVoteRequest
}

async function performVote ({ commit, state }, choice) {
  let priorVoteChoice = null
  if (state.currentVote) {
    priorVoteChoice = state.currentVote.choice
  }
  let fetchBody = new URLSearchParams()
  fetchBody.set('user_id', getUserId())
  fetchBody.set('choice', choice)
  fetchBody.set('level_key', state.currentLevel.key)
  let fetchOptions = {
    method: 'POST',
    body: fetchBody
  }
  let newCurrentVote = await fetchJson('/api/vote', fetchOptions)
  commit('setCurrentVote', newCurrentVote)
  commit('applyPredicitonToCurrentLevel', {
    oldChoice: priorVoteChoice,
    newChoice: choice
  })
}

let actions = {
  fetchCurrentLevel,
  fetchCurrentVote,
  performVote
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
