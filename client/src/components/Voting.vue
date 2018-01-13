<template>
  <div class="voting">
    <img src="src/assets/ryukahr_logo.png" class="ryulogo">
    <div v-if="noLevelInProgress">
      <h2>No Level</h2>
      <p>Looks like Ryukahr is not playing a level at the moment</p>
    </div>
    <div v-else-if="currentLevel">
      <h2 class="current-level-header">Vote on the level: {{currentLevel.name_ish }}</h2>
      <div class="votes-container">
        <div class="votes-item">
          <img src="src/assets/star_level_256.png" class="vote-image bounceIn" v-on:click.prevent="performVote('star')"/> 
          <p class="votes-item-text">{{currentLevelVotesDisplayValues.star}} votes ({{ starVotesPercent }}%)</p>
        </div>
        <div class="votes-item">
          <img src="src/assets/trash_button_256.png" class="vote-image bounceIn" v-on:click.prevent="performVote('garbage')"/>
          <p class="votes-item-text">{{currentLevelVotesDisplayValues.garbage}} votes ({{ garbageVotesPercent }}%)</p>
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
      let totalVotes = this.currentLevelVotesDisplayValues.star + this.currentLevelVotesDisplayValues.garbage
      if (totalVotes === 0) {
        return 0
      }
      return Math.round(100 * this.currentLevelVotesDisplayValues.star / totalVotes)
    },
    garbageVotesPercent () {
      let totalVotes = this.currentLevelVotesDisplayValues.star + this.currentLevelVotesDisplayValues.garbage
      if (totalVotes === 0) {
        return 0
      }
      return Math.round(100 * this.currentLevelVotesDisplayValues.garbage / totalVotes)
    },
    ...mapState([
      'currentLevel',
      'currentVote',
      'currentLevelVotesDisplayValues'
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
@import 'https://fonts.googleapis.com/css?family=Bowlby+One+SC';
.voting {
  height: 100vh;
  background-image: url("/src/assets/wallpaper.png");
  background-repeat:no-repeat;
  background-size:cover;
  font-family: 'Bowlby One SC', Helvetica, sans-serif;
}
h1, h2 {
  font-weight: normal;
  text-shadow: 2px 2px 5px red;
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
  color: #be3535;
}
.current-level-header {
  font-size: 200%;
  color: "#000000";
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
.vote-image {
  border-radius: 15px;
  background: rgb(56, 60, 77);
  padding: 20px; 
  width: 200px;
  height: 200px;
  cursor: pointer;
  box-shadow: 3px 10px;
  color:#be3535;
}
.votes-item-text {
  font-size: 120%;
}
@keyframes bounceIn {
  from, 20%, 40%, 60%, 80%, to {
    animation-timing-function: cubic-bezier(0.215, 0.610, 0.355, 1.000);
  }

  0% {
    opacity: 0;
    transform: scale3d(.3, .3, .3);
  }

  20% {
    transform: scale3d(1.1, 1.1, 1.1);
  }

  40% {
    transform: scale3d(.9, .9, .9);
  }

  60% {
    opacity: 1;
    transform: scale3d(1.03, 1.03, 1.03);
  }

  80% {
    transform: scale3d(.97, .97, .97);
  }

  to {
    opacity: 1;
    transform: scale3d(1, 1, 1);
  }
}
.bounceIn {
  animation-duration: .75s;
  animation-name: bounceIn;
}
</style>
