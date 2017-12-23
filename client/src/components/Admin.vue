<template>
  <div class="admin">
    <div class="loading" v-if="loading">
      Loading...
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="config" class="links">
      <a :href="config.login_url">Login</a>
      <a :href="config.logout_url">Logout</a>
    </div>
  </div>
</template>

<script>
export default {
  data () {
    return {
      loading: false,
      config: null,
      error: null
    }
  },
  created () {
    // fetch the data when the view is created and the data is
    // already being observed
    this.fetchData()
  },
  watch: {
    // call again the method if the route changes
    '$route': 'fetchData'
  },
  methods: {
    fetchData () {
      this.error = this.post = null
      this.loading = true
      fetch('/api/config')
      .then(response => {
        this.loading = false
        if (!response.ok) {
          throw new Error('Error from /api/config : ' + response.toString())
        }
        return response.json()
      })
      .then(config => {
        this.config = config
      })
      .catch(err => {
        this.loading = false
        this.error = err.toString()
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
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
