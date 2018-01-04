import os

from ndb_util import FancyModel
from google.appengine.ext import ndb


IS_PUBLIC_ENVIRONMENT = os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine')


class PersistentConfig(FancyModel):
    updated_timestamp = ndb.DateTimeProperty(auto_now=True)
    initial_num_shards_for_vote_counters = ndb.IntegerProperty(default=50)
    websocket_url = ndb.StringProperty(default='wss://gke.ryustar.io/websocket' if IS_PUBLIC_ENVIRONMENT else 'ws://gke.ryustar.invalid/websocket')

    @classmethod
    def get_singleton(cls):
        return cls.get_or_insert('singleton')

    def to_client_model(self):
        include = [
            'updated_timestamp',
            'websocket_url'
        ]
        return self.to_dict(include=include)
