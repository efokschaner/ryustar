import os

from ndb_util import FancyModel
from google.appengine.ext import ndb


IS_PUBLIC_ENVIRONMENT = os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine')

RECAPTCHA_MODES = ['disabled', 'test', 'production']

# These are the public test keys from https://developers.google.com/recaptcha/docs/faq
RECAPTCHA_TEST_SECRET_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
RECAPTCHA_TEST_SITE_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'


class PersistentConfig(FancyModel):
    updated_timestamp = ndb.DateTimeProperty(auto_now=True)
    initial_num_shards_for_vote_counters = ndb.IntegerProperty(default=256)
    websocket_url = ndb.StringProperty(
        default='wss://gke.ryustar.io/websocket' if IS_PUBLIC_ENVIRONMENT else 'ws://gke.ryustar.invalid/websocket')

    client_recaptcha_mode = ndb.StringProperty(default='test', choices=RECAPTCHA_MODES)
    server_recaptcha_mode = ndb.StringProperty(default='test', choices=RECAPTCHA_MODES)
    # This is to be populated with the secret key in the production datastore
    recaptcha_production_secret_key = ndb.StringProperty()
    recaptcha_production_site_key = ndb.StringProperty(default='6LdISj8UAAAAAHq_SsCfYviBIB1sZ0BKSDJfJFGQ')
    recaptcha_test_secret_key = ndb.StringProperty(default=RECAPTCHA_TEST_SECRET_KEY)
    recaptcha_test_site_key = ndb.StringProperty(default=RECAPTCHA_TEST_SITE_KEY)

    def to_client_model(self):
        include = [
            'client_recaptcha_mode',
            'recaptcha_production_site_key',
            'recaptcha_test_site_key',
            'updated_timestamp',
            'websocket_url'
        ]
        return self.to_dict(include=include)
