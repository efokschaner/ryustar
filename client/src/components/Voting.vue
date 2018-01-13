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
          <div class="votes-item">
            <img src="../assets/star_level_256.png" class="vote-image bounceIn" v-on:click.prevent="submitVote('star')"/>
            <p class="votes-text">{{currentLevelVotesDisplayValues.star}} votes ({{ starVotesPercent }}%)</p>
          </div>
          <div class="votes-item">
            <img src="../assets/trash_button_256.png" class="vote-image bounceIn" v-on:click.prevent="submitVote('garbage')"/>
            <p class="votes-item-text">{{currentLevelVotesDisplayValues.garbage}} votes ({{ garbageVotesPercent }}%)</p>
          </div>
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
export default {
  name: 'Voting',
  components: { VueRecaptcha },
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
    hasVoted (choice) {
      return this.currentVote && (this.currentVote.choice === choice)
    },
    starVotesPercent () {
      let totalVotes = this.currentLevelVotesDisplayValues.star + this.currentLevelVotesDisplayValues.garbage
      if (totalVotes === 0) {
        return 0
      }
      return Math.round(100 * this.currentLevelVotesDisplayValues.star / totalVotes)
    },
    garbageVotesPercent () {
      let totalVotes = this.currentLevelVotesDisplayValues.star + this.currentLevelVotesDisplayValues.garbage
      if (totalVotes === 0) {
        return 0
      }
      return Math.round(100 * this.currentLevelVotesDisplayValues.garbage / totalVotes)
    },
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
.votes-item {
  padding: 10px;
}
.vote-image {
  border-radius: 15px;
  background: rgb(56, 60, 77);
  padding: 20px;
  width: 200px;
  height: 200px;
  cursor: pointer;
  box-shadow: 3px 10px;
  color:#be3535;
}
.votes-item-text {
  font-size: 120%;
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
