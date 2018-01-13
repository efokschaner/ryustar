## UX
- ALL THE ERROR MESSAGES
- Admin pages
  - Change captcha config
- Vote request in progress

## Art
- Star button
- Garbage button

## Tech
- Investigate whether storing absence of new user's vote is better than not finding in data store each time.
- Gremlins test?
- Maybe have app engine act as an autoscaler for gke?
- Maybe allow votes to go through for recently finished level?
- Add datetime updated to GET current level. Compare to locustio client time to create rough "latency" metric
- Convert Websocket connection error from toast to dedicated status component.
- Investigate if display: none is functionally valid on the recaptcha
