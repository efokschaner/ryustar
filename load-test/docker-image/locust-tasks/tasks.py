#!/usr/bin/env python

from datetime import datetime
import json
import uuid

import gevent
from locust import events, HttpLocust, TaskSet, task
import ws4py.client.geventclient


class UserWithAccount(TaskSet):
    @task(1)
    def exit(self):
        self.parent.schedule_task(self.parent.exit)
        self.interrupt()

    @task(40)
    def just_hang_out(self):
        pass

    @task(10)
    def vote(self):
        # TODO IMPLEMENT
        pass


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


class RyuStarWebsocketClient(object):
    def __init__(self, url, user_state):
        self.url = url
        self.user_state = user_state
        self.stop_requested = False
        self.ws = ws4py.client.geventclient.WebSocketClient(self.url)
        self.greenlet = gevent.spawn(self.run_thread)

    def close(self):
        self.stop_requested = True
        self.ws.close(code=1001)
        gevent.with_timeout(10, gevent.joinall, [self.greenlet], raise_error=True)

    def run_thread(self):
        try:
            first_message = True
            self.ws.connect()
            while not self.stop_requested:
                m = self.ws.receive()
                if m is not None:
                    self.process_message(m)
                    # Process before logging the first success
                    if first_message:
                        events.request_success.fire(
                            request_type="websocket",
                            name=self.url,
                            response_time=0,
                            response_length=len(m.data)
                        )
                        first_message = False
                else:
                    if not self.stop_requested:
                        events.request_failure.fire(
                            request_type="websocket",
                            name=self.url,
                            response_time=0,
                            exception='unexpected_websocket_close_error'
                        )
                    break
        except Exception as e:
            events.request_failure.fire(
                request_type="websocket",
                name=self.url,
                response_time=0,
                exception=e
            )
            raise

    def process_message(self, m):
        message = json.loads(m.data)
        if message['url'] == '/api/level/current':
            self.user_state.current_level



class RyuStarUser(HttpLocust):
    task_set = RyuStarUserTaskSet
    min_wait = 2000
    max_wait = 5000

    def __init__(self, *args, **kwargs):
        super(RyuStarUser, self).__init__(*args, **kwargs)
        self.user_state = None
        self.ws_client = None

    def connect_ws_client(self, url):
        self.ws_client = RyuStarWebsocketClient(url, self.user_state)

    def close_ws_client(self):
        if self.ws_client:
            self.ws_client.close()
        self.ws_client = None

    def become_new_user(self):
        # In theory we should clear HttpLocust's session here but seeing
        # as RyuStar is not using cookies for its user logic I'm not gonna figure
        # out how to do that yet
        self.close_ws_client()
        self.user_state = UserState()

