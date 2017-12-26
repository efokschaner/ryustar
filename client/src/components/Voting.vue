<template>
  <div class="voting">
    <div v-if="noLevelInProgress">
      <h2>No Level</h2>
      <p>Looks like Ryukahr is not playing a level at the moment</p>
    </div>
    <div v-else-if="currentLevel">
      <h2>Vote on the level: {{currentLevel.name_ish}}</h2>
      <div class="votes-container">
        <div class="votes-item">
          <h3>Star</h3>
          <p>{{currentLevel.star_votes_count}} votes ({{ starVotesPercent }}%)</p>
          <a v-if="!hasVoted('star')" class="vote-link" v-on:click.prevent="performVote('star')">Vote</a>
        </div>
        <div>
          <h3>Garbage</h3>
          <p>{{currentLevel.garbage_votes_count}} votes ({{ garbageVotesPercent }}%)</p>
          <a v-if="!hasVoted('garbage')" class="vote-link" v-on:click.prevent="performVote('garbage')">Vote</a>
        </div>
      </div>
    </div>
    <div v-else>
      <h2>Fetching level info ...</h2>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
export default {
  name: 'Voting',
  created () {
    return this.$store.dispatch('fetchCurrentLevel').then(() => this.$store.dispatch('fetchCurrentVote'))
  },
  data () {
    return {
    }
  },
  computed: {
    starVotesPercent () {
      let curLevel = this.$store.state.currentLevel
      let totalVotes = curLevel.star_votes_count + curLevel.garbage_votes_count
      if (totalVotes === 0) {
        return 0
      }
      return Math.round(100 * curLevel.star_votes_count / totalVotes)
    },
    garbageVotesPercent () {
      let curLevel = this.$store.state.currentLevel
      let totalVotes = curLevel.star_votes_count + curLevel.garbage_votes_count
      if (totalVotes === 0) {
        return 0
      }
      return Math.round(100 * curLevel.garbage_votes_count / totalVotes)
    },
    ...mapState([
      'currentLevel',
      'currentVote'
    ]),
    ...mapGetters([
      'noLevelInProgress'
    ])
  },
  methods: {
    hasVoted (choice) {
      let curVote = this.$store.state.currentVote
      return curVote && (curVote.choice === choice)
    },
    ...mapActions([
      'performVote'
    ])
  }
}
</script>

<style scoped>
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.vote-link {
  cursor: pointer;
}
.votes-container{
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: baseline;
}
.votes-item {
  padding: 10px;
}
</style>
