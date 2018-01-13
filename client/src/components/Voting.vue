<template>
  <div class="voting">
    <img src="../assets/ryukahr_logo.png" class="ryulogo">
    <div v-if="noLevelInProgress">
      <h2>No Level</h2>
      <p>Looks like Ryukahr is not playing a level at the moment</p>
    </div>
    <div v-else-if="currentLevel">
      <div v-if="captchaConsentResolveCallback">
        <vue-recaptcha
            style="display: none"
            ref="invisibleRecaptcha"
            badge="inline"
            size="invisible"
            theme="dark"
            :sitekey="recaptchaSiteKey"
            @verify="onCaptchaVerify"
            @expired="onCaptchaExpired">
        </vue-recaptcha>
        <h3>This site uses Invisible ReCAPTCHA</h3>
        <p>To make sure that votes aren't being submitted by robots,
          this page uses Google's Invisible reCAPTCHA system for verifying that you are not a robot,
          or not a robot lacking human intelligence at least!
          reCAPTCHA works by "collecting hardware and software information,
          such as device and application data and the results of integrity checks,
          and sending that data to Google for analysis".
          Your use of Invisible reCAPTCHA is subject to Google's
          <a href="https://www.google.com/policies/privacy/">Privacy Policy</a> and
          <a href="https://www.google.com/policies/terms/">Terms of Use</a>
          Do you accept these terms, to continue with your vote?
        </p>
        <button @click="onRefusedCaptcha()">No thanks! I'll just spectate.</button>
        <button @click="onConsentToCaptcha()">I accept these terms and wish to vote!</button>
      </div>
      <div v-else>
        <h2 class="current-level-header">Vote on the level: {{currentLevel.name_ish }}</h2>
        <div class="votes-container">
          <vote-item choice="star" @chosen="submitVote('star')">
            <img src="../assets/star_level_256.png"/>
          </vote-item>
          <vote-item choice="garbage" @chosen="submitVote('garbage')">
            <img src="../assets/trash_button_256.png"/>
          </vote-item>
        </div>
      </div>
    </div>
    <div v-else>
      <h2>Fetching level info ...</h2>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import VueRecaptcha from 'vue-recaptcha'
import VoteItem from './VoteItem'
export default {
  name: 'Voting',
  components: { VueRecaptcha, VoteItem },
  created () {
    return Promise.all([
      this.fetchCurrentLevel(),
      this.fetchCurrentUser()
        .then(() => this.fetchCurrentVote())
    ])
    .catch((err) => {
      this.$toasted.global.genericError()
      throw err
    })
  },
  data () {
    return {
      captchaConsentResolveCallback: null
    }
  },
  computed: {
    ...mapState([
      'config',
      'currentUser',
      'currentLevel',
      'currentVote',
      'currentLevelVotesDisplayValues'
    ]),
    ...mapGetters([
      'noLevelInProgress',
      'recaptchaEnabled',
      'recaptchaSiteKey'
    ])
  },
  methods: {
    onConsentToCaptcha () {
      this.$refs.invisibleRecaptcha.execute()
    },
    onRefusedCaptcha () {
      this.captchaConsentResolveCallback({ hasConsent: false })
    },
    onCaptchaVerify (response) {
      this.captchaConsentResolveCallback({ hasConsent: true, recaptchaResponse: response })
    },
    onCaptchaExpired () {
      console.warn('Captcha expired')
      if (this.captchaConsentResolveCallback) {
        this.captchaConsentResolveCallback({ hasConsent: false })
      }
    },
    // Returns { hasConsent: boolean, recaptchaResponse: string? }
    async ensureConsent () {
      if (this.currentUser) {
        return { hasConsent: true }
      }
      if (!this.recaptchaEnabled) {
        return { hasConsent: true }
      }
      try {
        return await new Promise((resolve) => {
          this.captchaConsentResolveCallback = resolve
        })
      } finally {
        this.captchaConsentResolveCallback = null
      }
    },
    async ensureUser () {
      if (this.currentUser) {
        return
      }
      let { hasConsent, recaptchaResponse } = await this.ensureConsent()
      if (hasConsent) {
        return this.createUser({recaptchaResponse})
      }
    },
    async submitVote (choice) {
      try {
        await this.ensureUser()
        if (this.currentUser) {
          return this.performVote(choice)
        }
      } catch (err) {
        this.$toasted.global.genericError()
        throw err
      }
    },
    ...mapActions([
      'createUser',
      'fetchCurrentUser',
      'fetchCurrentLevel',
      'fetchCurrentVote',
      'performVote'
    ])
  }
}
</script>
<style scoped>
@import 'https://fonts.googleapis.com/css?family=Bowlby+One+SC';
.voting {
  height: 100vh;
  background-image: url("../assets/wallpaper.png");
  background-repeat:no-repeat;
  background-size:cover;
  font-family: 'Bowlby One SC', Helvetica, sans-serif;
  text-align: center;
}
h1, h2 {
  text-shadow: 2px 2px 5px red;
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
  color: #be3535;
}
.current-level-header {
  font-size: 200%;
  color: "#000000";
}
.votes-container{
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: baseline;
}
</style>
