import Vue from 'vue'
import Router from 'vue-router'
import Voting from '@/components/Voting'
import Admin from '@/components/Admin'

const NotFoundComponent = { template: `
<div>
  <h1>Not Found</h1>
  <p>
    The requested URL was not found.
    If you entered the URL manually please check your spelling and try again.
  </p>
<div>`
}

Vue.use(Router)

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      name: 'Voting',
      component: Voting
    },
    {
      path: '/admin/',
      name: 'Admin',
      component: Admin
    },
    {
      path: '*',
      component: NotFoundComponent
    }
  ]
})
