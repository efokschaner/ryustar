<template>
  <div class="admin">
    <div class="form-wrapper">
      <form v-on:submit.prevent="startNewLevel">
        <input v-model="newLevelNameIsh" type=text required="required" placeholder="Level Name (ish)">
        <input type="submit" class="btn btn-default" value="Start New Level">
      </form>
    </div>
    <div class="form-wrapper">
      <form v-on:submit.prevent="endCurrentLevel">
        <input type="submit" class="btn btn-default" value="End Current Level">
      </form>
    </div>
    <div class="form-wrapper">
      <form v-on:submit.prevent="increaseCounterShards">
        <input v-model.number="selectedNumShards" required="required" type="number">
        <input type="submit" class="btn btn-default" value="Change num counter shards">
      </form>
    </div>
    <div class="working" v-if="working">
      Working...
    </div>
    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
export default {
  data () {
    return {
      working: false,
      error: null,
      newLevelNameIsh: '',
      selectedNumShards: 0
    }
  },
  created () {
    return this.$store.dispatch('fetchCurrentLevel')
  },
  methods: {
    async startNewLevel () {
      this.error = null
      this.working = true
      let fetchBody = new URLSearchParams()
      fetchBody.set('name_ish', this.newLevelNameIsh)
      let fetchOptions = {
        method: 'POST',
        body: fetchBody,
        credentials: 'same-origin'
      }
      try {
        let response = await fetch('/api/admin/start-new-level', fetchOptions)
        if (!response.ok) {
          let errorText = await response.text()
          throw new Error(`HTTP ${response.status} from /api/admin/start-new-level : ${errorText}`)
        }
      } catch (err) {
        this.error = err.toString()
      } finally {
        this.working = false
      }
    },
    async endCurrentLevel () {
      this.error = null
      this.working = true
      let fetchOptions = {
        method: 'POST',
        credentials: 'same-origin'
      }
      try {
        let response = await fetch('/api/admin/end-current-level', fetchOptions)
        if (!response.ok) {
          let errorText = await response.text()
          throw new Error(`HTTP ${response.status} from /api/admin/start-new-level : ${errorText}`)
        }
      } catch (err) {
        this.error = err.toString()
      } finally {
        this.working = false
      }
    },
    async increaseCounterShards () {
      this.error = null
      this.working = true
      let fetchBody = new URLSearchParams()
      fetchBody.set('total_shards', this.selectedNumShards)
      let fetchOptions = {
        method: 'POST',
        body: fetchBody,
        credentials: 'same-origin'
      }
      try {
        let response = await fetch('/api/admin/increase-current-level-total-counter-shards', fetchOptions)
        if (!response.ok) {
          let errorText = await response.text()
          throw new Error(`HTTP ${response.status} from /api/admin/increase-current-level-total-counter-shards : ${errorText}`)
        }
      } catch (err) {
        this.error = err.toString()
      } finally {
        this.working = false
      }
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
.form-wrapper {
  padding: 5px
}
</style>
