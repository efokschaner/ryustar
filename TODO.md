## Pages
- Ryu is not playing a level right now
- Can't get current info
- Current level, unvoted
- Current level, voting star
- Current level, voting garbage
- Current level, voted star
- Current level, voted garbage
- Voting failed.
- Admin pages
  - Login
  - Clear current level and start new level
  - (Undo new level)?

## Art
- Star button
- Garbage button

## Tech
- locust.io load test on secong GKE cluster.
- Investigate whether storing absence of new user's vote is better than not finding in data store each time.
- Gremlins test?
- Maybe have app engine act as an autoscaler for gke?
