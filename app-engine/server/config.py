import os

from ndb_util import FancyModel
from google.appengine.ext import ndb


IS_PUBLIC_ENVIRONMENT = os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine')


class PersistentConfig(FancyModel):
    updated_timestamp = ndb.DateTimeProperty(auto_now=True)
    initial_num_shards_for_vote_counters = ndb.IntegerProperty(default=50)
    websocket_url = ndb.StringProperty(
        default='wss://gke.ryustar.io/websocket' if IS_PUBLIC_ENVIRONMENT else 'ws://gke.ryustar.invalid/websocket')
    # These defaults are the public test keys from https://developers.google.com/recaptcha/docs/faq
    recaptcha_site_key = ndb.StringProperty(default='6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
    recaptcha_secret_key = ndb.StringProperty(default='6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')
    client_recaptcha_enabled = ndb.BooleanProperty(default=True)
    server_recaptcha_enabled = ndb.BooleanProperty(default=True)
    def to_client_model(self):
        include = [
            'client_recaptcha_enabled',
            'recaptcha_site_key',
            'updated_timestamp',
            'websocket_url'
        ]
        return self.to_dict(include=include)
