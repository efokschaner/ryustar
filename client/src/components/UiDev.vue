<template>
  <div class="uidev">
    <input v-model="errorMessage" type=text placeholder="Error message">
    <button @click="doErrorToast()">Toast Error</button>
  </div>
</template>

<script>
export default {
  data () {
    return {
      errorMessage: ''
    }
  },
  created () {
  },
  methods: {
    doErrorToast () {
      this.$toasted.global.genericError({ message: this.errorMessage })
    }
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
.uidev {
  margin: 60px;
}
</style>
