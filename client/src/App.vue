<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'app',
  created () {
    return this.$store.dispatch('fetchConfig').catch((err) => {
      this.$toasted.global.genericError()
      throw err
    })
  }
}
</script>

<style lang="scss">
@import url('https://fonts.googleapis.com/css?family=Bowlby+One+SC|Ubuntu');
@font-face {
    font-family: 'Bou College';
    src: url('./fonts/boucollege-webfont.woff2') format('woff2'),
         url('./fonts/boucollege-webfont.woff') format('woff');
    font-weight: normal;
    font-style: normal;
}
#app {
  font-family: 'Ubuntu', Helvetica, sans-serif;
}
</style>
