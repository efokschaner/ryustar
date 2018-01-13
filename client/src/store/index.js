import { fetchJson } from '../fetch.js'
import { initWebsocketForStore } from './websocket'

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
  config: null,
  currentUser: null,
  currentLevel: null,
  hasSetCurrentLevel: false,
  currentVote: null,
  websocketHasError: false,
  currentLevelVotesDisplayValues: {
    star: 0,
    garbage: 0
  }
}

let getters = {
  noLevelInProgress (state) {
    return state.hasSetCurrentLevel && !state.currentLevel
  },
  recaptchaEnabled (state) {
    return state.config && (state.config.client_recaptcha_mode === 'production' || state.config.client_recaptcha_mode === 'test')
  },
  recaptchaSiteKey (state) {
    if (!state.config) {
      return null
    }
    if (state.config.client_recaptcha_mode === 'production') {
      return state.config.recaptcha_production_site_key
    }
    if (state.config.client_recaptcha_mode === 'test') {
      return state.config.recaptcha_test_site_key
    }
    return null
  }
}

function lerp (start, end, factor) {
  return start + ((end - start) * factor)
}

let activeLerp = null
function updateLerp ({commit, state}) {
  if (activeLerp) {
    let lerpFactor = (Date.now() - activeLerp.startTimeMS) / activeLerp.durationMS
    let activeLerpRef = activeLerp
    if (lerpFactor >= 1) {
      lerpFactor = 1
      activeLerp = null
    }
    let newValues = {
      star: lerp(activeLerpRef.startValues.star, state.currentLevel.star_votes_count, lerpFactor),
      garbage: lerp(activeLerpRef.startValues.garbage, state.currentLevel.garbage_votes_count, lerpFactor)
    }
    commit('setCurrentLevelVotesDisplayValues', newValues)
  }
  setTimeout(() => updateLerp({commit, state}), 100)
}

function setCurrentLevel (state, newCurrentLevel) {
  // if the current level changes, counts are 0, stop lerping
  if (!state.currentLevel || !newCurrentLevel || state.currentLevel.key !== newCurrentLevel.key) {
    state.currentLevelVotesDisplayValues.star = 0
    state.currentLevelVotesDisplayValues.garbage = 0
    activeLerp = null
  }
  if (newCurrentLevel) {
    activeLerp = {
      startTimeMS: Date.now(),
      durationMS: 1000,
      startValues: {
        star: state.currentLevelVotesDisplayValues.star,
        garbage: state.currentLevelVotesDisplayValues.garbage
      }
    }
  }
  // Updates can be out of order but if current level is not matching the current vote
  // Then we wipe current vote
  if (!newCurrentLevel || !state.currentVote || newCurrentLevel.key !== state.currentVote.level_key) {
    state.currentVote = null
  }
  state.currentLevel = newCurrentLevel
  state.hasSetCurrentLevel = true
}

let mutations = {
  setConfig (state, newConfig) {
    state.config = newConfig
  },
  setCurrentUser (state, newCurrentUser) {
    state.currentUser = newCurrentUser
  },
  setCurrentLevel,
  applyPredicitonToCurrentLevel (state, {oldChoice, newChoice}) {
    state.currentLevel[newChoice + '_votes_count'] += 1
    if (activeLerp) {
      activeLerp.startValues[newChoice] += 1
    }
    state.currentLevelVotesDisplayValues[newChoice] += 1
    let oldKey = oldChoice + '_votes_count'
    if (oldKey in state.currentLevel) {
      state.currentLevel[oldKey] -= 1
      if (activeLerp) {
        activeLerp.startValues[oldChoice] -= 1
      }
      state.currentLevelVotesDisplayValues[oldChoice] -= 1
    }
  },
  setCurrentVote (state, newCurrentVote) {
    state.currentVote = newCurrentVote
  },
  setWebSocketHasError (state, newWebSocketHasError) {
    state.websocketHasError = newWebSocketHasError
  },
  setCurrentLevelVotesDisplayValues (state, newValues) {
    state.currentLevelVotesDisplayValues.star = Math.round(newValues.star)
    state.currentLevelVotesDisplayValues.garbage = Math.round(newValues.garbage)
  }
}

async function createUser ({ commit }, { recaptchaResponse }) {
  let fetchBody = new URLSearchParams()
  fetchBody.set('g-recaptcha-response', recaptchaResponse)
  let fetchOptions = {
    method: 'POST',
    body: fetchBody
  }
  let newCurrentUser = await fetchJson(`/api/user/${getUserId()}/create`, fetchOptions)
  commit('setCurrentUser', newCurrentUser)
  return newCurrentUser
}

function dedupedAsyncCall (func) {
  let pendingPromise = null
  return function () {
    if (!pendingPromise) {
      pendingPromise = func.apply(this, arguments)
      pendingPromise.finally(() => { pendingPromise = null })
    }
    return pendingPromise
  }
}

let fetchConfig = dedupedAsyncCall(async function ({ commit }) {
  let newConfig = await fetchJson('/api/config')
  commit('setConfig', newConfig)
  return newConfig
})

let fetchCurrentUser = dedupedAsyncCall(async function ({ commit }) {
  let newCurrentUser = await fetchJson(`/api/user/${getUserId()}`)
  commit('setCurrentUser', newCurrentUser)
  return newCurrentUser
})

let fetchCurrentLevel = dedupedAsyncCall(async function ({ commit }) {
  let newCurrentLevel = await fetchJson('/api/level/current')
  commit('setCurrentLevel', newCurrentLevel)
  return newCurrentLevel
})

let fetchCurrentVote = dedupedAsyncCall(async function ({ commit, state }) {
  if (!state.currentUser) {
    return
  }
  let newCurrentVote = await fetchJson('/api/vote/' + state.currentUser.id)
  commit('setCurrentVote', newCurrentVote)
  return newCurrentVote
})

async function performVote ({ commit, state }, choice) {
  if (!state.currentUser) {
    throw new Error('Cant perform vote without a user id')
  }
  let priorVoteChoice = null
  if (state.currentVote) {
    priorVoteChoice = state.currentVote.choice
  }
  let fetchBody = new URLSearchParams()
  fetchBody.set('user_id', state.currentUser.id)
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
  createUser,
  fetchConfig,
  fetchCurrentUser,
  fetchCurrentLevel,
  fetchCurrentVote,
  performVote,
  updateLerp
}

let modules = {}

let store = new Vuex.Store({
  actions,
  getters,
  modules,
  mutations,
  state,
  strict: debug,
  plugins: debug ? [createLogger()] : []
})

store.dispatch('updateLerp')
initWebsocketForStore(store)

export default store
