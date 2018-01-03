import { fetchJson } from '../fetch.js'

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
  noLevelInProgress: state => {
    return state.hasSetCurrentLevel && !state.currentLevel
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
  setTimeout(() => updateLerp({commit, state}), 50)
}

function setCurrentLevel (state, newCurrentLevel) {
  // if the current level changes, current vote is null, counts are 0, stop lerping
  if (!state.currentLevel || !newCurrentLevel || state.currentLevel.key !== newCurrentLevel.key) {
    state.currentVote = null
    state.currentLevelVotesDisplayValues.star = 0
    state.currentLevelVotesDisplayValues.garbage = 0
    activeLerp = null
  }
  if (newCurrentLevel) {
    activeLerp = {
      startTimeMS: Date.now(),
      durationMS: state.currentLevel ? 1500 : 1000, // Lerp faster if this is the first update
      startValues: {
        star: state.currentLevelVotesDisplayValues.star,
        garbage: state.currentLevelVotesDisplayValues.garbage
      }
    }
  }
  state.currentLevel = newCurrentLevel
  state.hasSetCurrentLevel = true
}

let mutations = {
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

export default store
