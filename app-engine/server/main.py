import datetime
import json
import logging
import os
import urllib

from flask import Flask, jsonify, make_response, request

from google.appengine.api import urlfetch, users
from google.appengine.ext import ndb

import config
from flask_util import cache_for_seconds, get_view_function
from ndb_util import FancyModel
import pubsub
from sharded_counter import ShardedCounter


class Level(FancyModel):
    name_ish = ndb.StringProperty(required=True)
    start_time = ndb.DateTimeProperty(auto_now_add=True)
    end_time = ndb.DateTimeProperty()
    star_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    garbage_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    updated_timestamp = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create(cls, name_ish):
        num_shards = config.PersistentConfig.get_singleton().initial_num_shards_for_vote_counters
        star_votes_counter = ShardedCounter.create(num_shards)
        garbage_votes_counter = ShardedCounter.create(num_shards)
        level = cls()
        level.star_votes_counter_key = star_votes_counter.key
        level.garbage_votes_counter_key = garbage_votes_counter.key
        level.name_ish = name_ish
        level.put()
        return level

    def _to_client_model_shared(self):
        exclude = [
            'star_votes_counter_key',
            'garbage_votes_counter_key'
        ]
        return self.to_dict(exclude=exclude)

    def to_client_model_fast(self):
        level_dict = self._to_client_model_shared()
        level_dict['star_votes_count'] = self.star_votes_counter_key.get().get_count_fast()
        level_dict['garbage_votes_count'] = self.garbage_votes_counter_key.get().get_count_fast()
        return level_dict

    def to_client_model_exact(self):
        level_dict = self._to_client_model_shared()
        level_dict['star_votes_count'] = self.star_votes_counter_key.get().get_count_exact()
        level_dict['garbage_votes_count'] = self.garbage_votes_counter_key.get().get_count_exact()
        return level_dict


class CurrentLevel(FancyModel):
    level_key = ndb.KeyProperty()


def set_current_level(level):
    cur_level = CurrentLevel.get_singleton()
    if level is None:
        cur_level.level_key = None
    else:
        cur_level.level_key = level.key
    cur_level.put()
    pubsub.schedule_publish_endpoint('/api/level/current')


def get_current_level():
    cur_level_key =  CurrentLevel.get_singleton().level_key
    if cur_level_key is None:
        return None
    return cur_level_key.get()


def finish_current_level():
    cur_level = get_current_level()
    if cur_level is not None:
        cur_level.end_time = datetime.datetime.now()
        cur_level.put()


class User(FancyModel):
    creation_timestamp = ndb.DateTimeProperty(auto_now_add=True)

    def to_client_model(self):
        include = [
            'creation_timestamp',
        ]
        user_dict = self.to_dict(include=include)
        user_dict['id'] = self.key.id()
        return user_dict


class UserVote(FancyModel):
    user_id = ndb.StringProperty()
    level_key = ndb.KeyProperty()
    choice = ndb.StringProperty(choices=['star', 'garbage'])

    @classmethod
    def create(cls, user_id, level_key):
        new_vote = UserVote(key=cls.get_key(user_id, level_key))
        new_vote.user_id = user_id
        new_vote.level_key = level_key
        return new_vote

    @classmethod
    def get_key(cls, user_id, level_key):
        return ndb.Key(UserVote, '{}-{}'.format(level_key.urlsafe(), user_id))


def get_user_vote_on_level(user_id, level):
    if level is None:
        return None
    return UserVote.get_key(user_id, level.key).get()


def get_current_vote(user_id):
    return get_user_vote_on_level(user_id, get_current_level())


app = Flask(__name__)


@app.route('/api/config')
@cache_for_seconds(30)
def handle_get_config():
    conf = config.PersistentConfig.get_singleton()
    client_conf = conf.to_client_model()
    client_conf['login_url'] = users.create_login_url('/admin/')
    client_conf['logout_url'] = users.create_logout_url('/')
    return jsonify(client_conf)


@app.route('/api/level/current')
@cache_for_seconds(5)
def handle_get_current_level():
    cur_level = get_current_level()
    if cur_level is None:
        return jsonify(None)
    return jsonify(cur_level.to_client_model_fast())


@app.route('/api/vote/<user_id>')
@cache_for_seconds(10)
def handle_get_current_vote(user_id):
    cur_vote = get_current_vote(user_id)
    if cur_vote is not None:
        cur_vote = cur_vote.to_dict()
    return jsonify(cur_vote)


@app.route('/api/user/<user_id>')
@cache_for_seconds(10)
def handle_get_user(user_id):
    maybe_user = User.get_by_id(user_id)
    if maybe_user:
        user = maybe_user.to_client_model()
    else:
        user = None
    return jsonify(user)


@app.route('/api/user/<user_id>/create', methods=['POST'])
def handle_create_user(user_id):
    # first verify the captcha if needed:
    conf = config.PersistentConfig.get_singleton()
    if conf.server_recaptcha_enabled:
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            return 'Missing g-recaptcha-response', 400
        verify_payload = urllib.urlencode({
            'secret': conf.recaptcha_secret_key,
            'response': recaptcha_response,
            'remoteip': os.environ.get('REMOTE_ADDR')
        })
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        verify_response = urlfetch.fetch(
            verify_url,
            deadline=10, # seconds
            method=urlfetch.POST,
            payload=verify_payload,
            headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
            validate_certificate=True
        )
        if (not verify_response) or verify_response.status_code != 200:
            error_message = 'HTTP {} returned from POST to {}\n response={}'.format(
                verify_response.status_code,
                verify_url,
                repr(verify_response.__dict__)
            )
            raise Exception(error_message)
        verify_response_payload = json.loads(verify_response.content)
        if not verify_response_payload['success']:
            logging.info('Failed recaptcha: {}'.format(verify_response.content))
            return 'Recaptcha did not pass verification', 400

    user = User.get_or_insert(user_id)
    return jsonify(user.to_client_model())


class CommitVoteResult(object):
    def __init__(self, flask_response, counts_need_update=False):
        self.flask_response = flask_response
        self.counts_need_update = counts_need_update


@ndb.transactional(xg=True)
def commit_vote_transact(
        user_id,
        choice,
        cur_level,
        cur_level_star_votes_counter,
        cur_level_garbage_votes_counter):
    prior_vote = get_user_vote_on_level(user_id, cur_level)
    if prior_vote is not None:
        prior_vote_choice = prior_vote.choice
        if prior_vote_choice == choice:
            return CommitVoteResult(jsonify(prior_vote.to_dict()))
        new_vote = prior_vote
    else:
        prior_vote_choice = None
        new_vote = UserVote.create(user_id, cur_level.key)
    new_vote.choice = choice
    new_vote.put()
    if choice == 'star':
        cur_level_star_votes_counter.increment()
    elif choice == 'garbage':
        cur_level_garbage_votes_counter.increment()
    else:
        raise AssertionError('Should not be possible to reach here with invalid choice {}'.format(choice))
    if prior_vote_choice == 'star':
        cur_level_star_votes_counter.decrement()
    elif prior_vote_choice == 'garbage':
        cur_level_garbage_votes_counter.decrement()
    return CommitVoteResult(jsonify(new_vote.to_dict()), counts_need_update=True)


def commit_vote(user_id, choice, level_key):
    # confirm user_id is valid
    maybe_user = User.get_by_id(user_id)
    if not maybe_user:
        return CommitVoteResult(('No user found for id {}'.format(user_id), 400))
    # confirm level id is current
    cur_level = get_current_level()
    if cur_level is None:
        return CommitVoteResult(('No current level to vote on', 400))
    if cur_level.key != level_key:
        return CommitVoteResult((
            'Cannot vote on level {} as it is not the current level ({})'.format(
                level_key.urlsafe(),
                cur_level.key.urlsafe()),
            400))
    return commit_vote_transact(
        user_id,
        choice,
        cur_level,
        cur_level.star_votes_counter_key.get(),
        cur_level.garbage_votes_counter_key.get())


@app.route('/api/vote', methods=['POST'])
def handle_vote():
    user_id = request.form.get('user_id')
    if not user_id:
        return 'Missing user_id', 400
    choice = request.form.get('choice')
    if not choice:
        return 'Missing choice', 400
    urlsafe_level_key = request.form.get('level_key')
    if not urlsafe_level_key:
        return 'Missing level_key', 400
    level_key = ndb.Key(urlsafe=urlsafe_level_key)
    commit_vote_result = commit_vote(user_id, choice, level_key)
    if commit_vote_result.counts_need_update:
        pubsub.schedule_publish_endpoint('/api/level/current')
    return commit_vote_result.flask_response


@app.route('/api/admin/start-new-level', methods=['POST'])
def handle_start_new_level():
    finish_current_level()
    new_level = Level.create(request.form['name_ish'])
    set_current_level(new_level)
    return ('', 200)


@app.route('/api/admin/end-current-level', methods=['POST'])
def handle_end_current_level():
    finish_current_level()
    set_current_level(None)
    return ('', 200)


@app.route('/api/admin/publish-endpoint', methods=['POST'])
def handle_publish_endpoint():
    url = request.form.get('url')
    if not url:
        return 'Missing url', 400

    func_and_arg_data = get_view_function(app, url)
    if not func_and_arg_data:
        return 'Could not get func for url {}'.format(url), 400
    func = func_and_arg_data[0]
    resp = make_response(func())
    publish_payload = {
        'url': url,
        'body': resp.get_data()
    }
    pubsub.publish('ryustar-io-endpoints-topic', publish_payload)
    return ('', 200)


@app.route('/api/admin/increase-current-level-total-counter-shards', methods=['POST'])
def handle_increase_current_level_total_counter_shards():
    total_shards = request.form.get('total_shards')
    if not total_shards:
        return 'Missing total_shards', 400
    total_shards_int = int(total_shards)
    cur_level = get_current_level()
    cur_level.star_votes_counter_key.get().increase_total_shards(total_shards_int)
    cur_level.garbage_votes_counter_key.get().increase_total_shards(total_shards_int)
    return ('', 200)


@app.route('/api/admin/environ')
def handle_get_environ():
    def _sanitize(val):
        if isinstance(val, basestring):
            return val
        else:
            return repr(val)
    return jsonify({k:_sanitize(v) for k,v in os.environ.items()})


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

