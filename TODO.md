## UX
- ALL THE ERROR MESSAGES
- Admin pages
  - Change captcha config
- Vote request in progress

## Art
- Star button
- Garbage button

## Tech
- minikube container name can be the same as public name, fix websocket-service!
- Investigate whether storing absence of new user's vote is better than not finding in data store each time.
- Gremlins test?
- Maybe have app engine act as an autoscaler for gke?
- Allow secret and test recaptcha keys to co-exist in persistent config to make switching captcha mode easier:
  - Prod
  - Test
  - Disabled
  - Probably should write down instructions on safely switching between in light of clients + caching
- Maybe allow votes to go through for recently finished level?
