<template>
  <div class="voting">
    <div v-if="noLevelInProgress">
      <h2>No Level</h2>
      <p>Looks like Ryukahr is not playing a level at the moment</p>
    </div>
    <div v-else>
      <h2>Vote on the level</h2>

    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
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
    ...mapGetters([
      'noLevelInProgress'
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
</style>
