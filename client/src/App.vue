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

<style>
#app {

}
</style>
