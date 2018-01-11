import random
import sys
import uuid

import gevent
from locust import events, HttpLocust, TaskSet, task

from ws import RyuStarReconnectingWebsocketClient


class UserWithAccount(TaskSet):
    def on_start(self):
        # Client creates account when user chooses to vote
        # So always perform a vote immediately when entering this state
        self.vote()

    @task(1)
    def exit(self):
        self.parent.schedule_task(self.parent.exit)
        self.interrupt()

    @task(30)
    def just_hang_out(self):
        pass

    @task(5)
    def vote(self):
        if not self.locust.user_state.current_level:
            return
        if self.locust.user_state.current_vote:
            target_choice = 'garbage' if self.locust.user_state.current_vote.get('choice') == 'star' else 'star'
        else:
            target_choice = 'star' if random.random() < 0.5 else 'garbage'
        vote_response = self.client.post(
            '/api/vote',
            {
                'user_id': self.locust.user_state.id,
                'choice': target_choice,
                'level_key': self.locust.user_state.current_level['key']
            }
        )
        if vote_response.status_code == 200:
            self.locust.user_state.current_vote = vote_response.json()


class UserOnSite(TaskSet):
    def on_start(self):
        config_response = self.client.get('/api/config')
        self.locust.user_state.config = config_response.json()
        self.locust.connect_ws_client(self.locust.user_state.config['websocket_url'])
        current_level_response = self.client.get('/api/level/current')
        self.locust.user_state.current_level = current_level_response.json()
        user_response = self.client.get('/api/user/' + self.locust.user_state.id, name='/api/user/[id]')
        self.locust.user_state.user = user_response.json()
        if self.locust.user_state.user:
            current_vote_response = self.client.get('/api/vote/' + self.locust.user_state.id, name='/api/vote/[id]')
            self.locust.user_state.current_vote = current_vote_response.json()
            self.schedule_task(UserWithAccount)

    @task(1)
    def exit(self):
        self.locust.close_ws_client()
        self.interrupt()

    @task(85)
    def just_hang_out(self):
        pass

    @task(15)
    def create_account(self):
        user_create_response = self.client.post(
            '/api/user/' + self.locust.user_state.id + '/create',
            { 'g-recaptcha-response': '42' },
            name='/api/user/[id]/create'
        )
        self.locust.user_state.user = user_create_response.json()
        self.schedule_task(UserWithAccount)


class RyuStarUserTaskSet(TaskSet):
    def on_start(self):
        self.locust.become_new_user()

    @task(1)
    def remain_current_user(self):
        self.schedule_task(UserOnSite)

    @task(3)
    def become_new_user(self):
        self.locust.become_new_user()
        self.schedule_task(UserOnSite)


class UserState(object):
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.config = None
        self.current_level = None
        self.user = None
        self.current_vote = None


class RyuStarUser(HttpLocust):
    task_set = RyuStarUserTaskSet
    min_wait = 2000
    max_wait = 5000

    def __init__(self, *args, **kwargs):
        super(RyuStarUser, self).__init__(*args, **kwargs)
        self.user_state = None
        self.ws_client = None
        # This is like a finally clause for the entire Locust to ensure its websocket client is shutdown
        gevent.getcurrent().link(self.on_greenlet_completion)

    def connect_ws_client(self, url):
        self.ws_client = RyuStarReconnectingWebsocketClient(url, self.user_state, self.record_exception)

    def close_ws_client(self):
        if self.ws_client:
            self.ws_client.close()
        self.ws_client = None

    def become_new_user(self):
        self.client.cookies.clear()
        self.close_ws_client()
        self.user_state = UserState()

    def on_greenlet_completion(self, greenlet):
        self.close_ws_client()

    def record_exception(self, e):
        events.locust_error.fire(locust_instance=self, exception=e, tb=sys.exc_info()[2])
