<template>
  <div class="vote-item">
    <div class="vote-button bounceIn" v-on:click.prevent="$emit('chosen')">
      <mario-block>
        <div class="block-content">
          <div class="image-wrapper">
            <slot>
            </slot>
          </div>
          <div class="hover-text">{{hoverText}}</div>
        </div>
      </mario-block>
    </div>
    <div class="counter-container">
      <h2 class="counter-stat">{{ currentLevelVotesDisplayValues[this.choice] }} votes</h2>
      <h2 class="counter-stat">{{ votesPercent(choice) }}%</h2>
    </div>
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
    'choice',
    'hoverText'
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
<style lang="scss" scoped>
@import '../base.scss';
.vote-item {
  margin: 0 15px;
}
.vote-button {
  cursor: pointer;
  &:hover {
    .image-wrapper {
      opacity: 0.4;
    }
    .hover-text {
      opacity: 1;
    }
  }
}
.block-content {
  position: relative;
}
.image-wrapper {
   margin: 10px;
}
.hover-text {
  opacity: 0;
  font-size: 200%;
  position: absolute;
  top: 0%;
  left: 0%;
  width: 100%;
  height: 100%;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}
.counter-container {
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}
.counter-stat {
  margin: 10px 0px;
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
