<template>
  <div class="vote-item">
    <div class="vote-image bounceIn" v-on:click.prevent="$emit('chosen')">
      <slot>
      </slot>
    </div>
    <p class="vote-item-text">{{currentLevelVotesDisplayValues[this.choice]}} votes ({{ votesPercent(choice) }}%)</p>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
export default {
  name: 'VoteItem',
  components: {},
  props: [
    'choice'
  ],
  created () {
  },
  data () {
    return {
    }
  },
  computed: {
    ...mapState([
      'currentLevelVotesDisplayValues'
    ]),
    ...mapGetters([
      'hasVoted',
      'votesPercent'
    ])
  },
  methods: {
    ...mapActions([
    ])
  }
}
</script>
<style scoped>
.vote-item {
  padding: 10px;
}
.vote-image {
  border-radius: 15px;
  background: rgb(56, 60, 77);
  padding: 20px;
  cursor: pointer;
  box-shadow: 3px 10px;
  color:#be3535;
}
.vote-item-text {
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
