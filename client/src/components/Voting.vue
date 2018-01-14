<template>
  <div class="voting-scene">
    <div class="voting-ui">
      <mario-block class="logo">
        <!-- Hacky Kerning fix incoming -->
        <span class="logo-text">RyuS<span style="letter-spacing: -4px;">t</span>ar.io</span>
      </mario-block>
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
            this page uses Google's Invisible reCAPTCHA system for verifying that you are not a robot &mdash;
            or not a robot lacking human intelligence at least! &mdash;
            reCAPTCHA works by "collecting hardware and software information,
            such as device and application data and the results of integrity checks,
            and sending that data to Google for analysis".
            Your use of Invisible reCAPTCHA is subject to Google's
            <a href="https://www.google.com/policies/privacy/">Privacy Policy</a> and
            <a href="https://www.google.com/policies/terms/">Terms of Use</a>.</p>
            <p>Do you accept these terms?</p>
          <button @click="onRefusedCaptcha()">No thanks! I'll just spectate...</button>
          <button @click="onConsentToCaptcha()">I accept these terms and wish to vote!</button>
        </div>
        <div v-else>
          <h4>Now voting on:</h4>
          <h2>{{ currentLevel.name_ish }}</h2>
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
    <div class="ground-texture">
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import VueRecaptcha from 'vue-recaptcha'
import MarioBlock from './MarioBlock'
import VoteItem from './VoteItem'
export default {
  name: 'Voting',
  components: {
    MarioBlock,
    VueRecaptcha,
    VoteItem
  },
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
<style lang="scss" scoped>

$text-color: rgb(0, 0, 11);
$text-highlight-color: rgb(255, 182, 55);

.voting-scene {
  min-height: 100vh;
  background: linear-gradient(rgb(63, 97, 233), rgba(63, 97, 233, 0.6));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  color: $text-color;
}
.voting-ui {
  padding: 30px;
  max-width: 860px;
}
.logo {
  text-align: left;
}
.logo-text {
  font-family: 'Bou College', Helvetica, sans-serif;
  font-size: 300%;
  padding: 0 10px;
}
h1, h2, h3, h4, h5, h6 {
  font-family: 'Bowlby One SC', Helvetica, sans-serif;
  letter-spacing: 0.09em;
  color: $text-highlight-color;
  text-shadow: 3px 3px 3px $text-color;
}
a {
  color: $text-highlight-color;
}
.votes-container{
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: baseline;
}
.ground-texture{
  height: 57px;
  width: 100%;
  background-image: url('../assets/floor.png');
  background-repeat: repeat-x;
}
</style>
