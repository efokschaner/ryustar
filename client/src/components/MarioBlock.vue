<template>
  <div :class="{ grid: !isHit, 'grid-hit': isHit }">
    <div class="cell-top-left"></div>
    <div class="cell-top-middle"></div>
    <div class="cell-top-right"></div>
    <div class="cell-middle-left"></div>
    <div class="cell-middle-middle">
      <slot></slot>
    </div>
    <div class="cell-middle-right"></div>
    <div class="cell-bottom-left"></div>
    <div class="cell-bottom-middle"></div>
    <div class="cell-bottom-right"></div>
  </div>
</template>

<script>
export default {
  name: 'MarioBlock',
  components: {},
  props: {
    isHit: {
      type: Boolean,
      default: false
    }
  },
  created () {
  },
  data () {
    return {
    }
  },
  computed: {
  },
  methods: {
  }
}
</script>
<style lang="scss" scoped>
$light-edge: rgb(237, 115, 28);
$dark-edge: rgb(0, 0, 11);
$center: rgb(253, 206, 127);
$center-hit: rgb(158,74,1);
$edge-width: 6px;

.grid-common {
  display: inline-grid;
  grid-template-rows: $edge-width 1fr $edge-width;
  grid-template-columns: $edge-width 1fr $edge-width;
  justify-content: start;
  align-content: start;
  justify-items: stretch;
  align-items: stretch;
}

.grid {
  @extend .grid-common;

  .cell-middle-middle {
      background-color: $center;
  }

  .cell-top-left {
  }
  .cell-top-middle  {
      background-color: $light-edge;
  }
  .cell-top-right {
  }
  .cell-middle-left {
      background-color: $light-edge;
  }
  .cell-middle-right {
      background-color: $dark-edge;
  }
  .cell-bottom-left {
      background-color: $dark-edge;
  }
  .cell-bottom-middle {
      background-color: $dark-edge;
  }
  .cell-bottom-right {
      background-color: $dark-edge;
  }

  &:active {
    .cell-top-left {
    }
    .cell-top-middle  {
        background-color: $dark-edge;
    }
    .cell-top-right {
    }
    .cell-middle-left {
        background-color: $dark-edge;
    }
    .cell-middle-right {
        background-color: $light-edge;
    }
    .cell-bottom-left {
        background-color: $light-edge;
    }
    .cell-bottom-middle {
        background-color: $light-edge;
    }
    .cell-bottom-right {
      background-color: $light-edge;
    }
  }
}

.grid-hit {
  @extend .grid-common;
  
  .cell-middle-middle {
    background-color: $center-hit;
  }

  .cell-top-left {
  }
  .cell-top-middle  {
      background-color: $dark-edge;
  }
  .cell-top-right {
  }
  .cell-middle-left {
      background-color: $dark-edge;
  }
  .cell-middle-right {
      background-color: $dark-edge;
  }
  .cell-bottom-left {
      background-color: $dark-edge;
  }
  .cell-bottom-middle {
      background-color: $dark-edge;
  }
  .cell-bottom-right {
      background-color: $dark-edge;
  }
}

</style>
