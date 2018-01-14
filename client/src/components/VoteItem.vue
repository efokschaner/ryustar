<template>
  <div class="vote-item">
    <div class="vote-button bounceIn" v-on:click.prevent="$emit('chosen')">
      <mario-block>
        <slot>
        </slot>
        
      </mario-block>
    </div>
    <p class="vote-item-text">{{currentLevelVotesDisplayValues[this.choice]}} votes ({{ votesPercent(choice) }}%)</p>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import MarioBlock from './MarioBlock'
export default {
  name: 'VoteItem',
  components: {
    MarioBlock
  },
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
@import '../base.scss';
.vote-item {
  margin: 0 15px;
}
.vote-button {
  cursor: pointer;
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
