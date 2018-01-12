import json
import random
import time

import gevent
from locust import events
import ws4py.client.geventclient


class WebSocketClient(ws4py.client.geventclient.WebSocketClient):
    """ Derive so we can capture the closed reason """
    def __init__(self, *args, **kwargs):
        super(WebSocketClient, self).__init__(*args, **kwargs)
        self.close_code = None
        self.close_reason = None

    def closed(self, code, reason=None):
        self.close_code = code
        self.close_reason = reason
        super(WebSocketClient, self).closed(code, reason=reason)


class UnexpectedWebsocketCloseError(Exception):
    pass


class RyuStarReconnectingWebsocketClient(object):
    def __init__(self, url, user_state, record_exception):
        self.url = url
        self.user_state = user_state
        self._record_exception = record_exception
        self.stop_requested = False
        self.ws = None
        self.greenlet = gevent.spawn(self._run_thread)

    def close(self):
        self.stop_requested = True
        if self.ws:
            self.ws.messages.put(StopIteration)
        gevent.with_timeout(10, gevent.joinall, [self.greenlet], raise_error=True)

    def _close_ws(self):
        if self.ws and not (self.ws.terminated or self.ws.sock is None):
            self.ws.close(code=1001, reason='locust client disconnecting')

    def _run_one_websocket_connection(self):
        first_message = True
        self.ws = WebSocketClient(self.url)
        try:
            self.ws.connect()
            while not self.stop_requested:
                m = self.ws.receive()
                if m is not None:
                    self._process_message(m)
                    # Process before logging the first success
                    if first_message:
                        events.request_success.fire(
                            request_type="websocket",
                            name=self.url,
                            response_time=0,
                            response_length=len(m.data))
                        first_message = False
                else:
                    if not self.stop_requested:
                        message = 'UnexpectedWebsocketCloseError: Code: {}. Reason: {}'.format(
                            self.ws.close_code,
                            self.ws.close_reason)
                        raise UnexpectedWebsocketCloseError(message)
        finally:
            try:
                self._close_ws()
            except Exception as e:
                self._record_exception(e)

    def _run_thread(self):
        while not self.stop_requested:
            try:
                self._run_one_websocket_connection()
            except Exception as e:
                events.request_failure.fire(
                    request_type="websocket",
                    name=self.url,
                    response_time=0,
                    exception=e)
                self._record_exception(e)
            if not self.stop_requested:
                # This is a dumber, more aggressive reconnect loop than in production
                # but isn't that what load tests are for? :P
                time.sleep(random.random() * 20)

    def _process_message(self, m):
        message = json.loads(m.data)
        if message['url'] == '/api/level/current':
            self.user_state.current_level = json.loads(message['body'])
            if (not self.user_state.current_vote
                    or not self.user_state.current_level
                    or self.user_state.current_vote['level_key'] != self.user_state.current_level['key']):
                self.user_state.current_vote = None
