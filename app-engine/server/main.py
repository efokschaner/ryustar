import datetime
import logging
import os
from urlparse import urlparse, urlunparse

from flask import Flask, jsonify, request
import flask.json

from google.appengine.api import app_identity, urlfetch, users, taskqueue
from google.appengine.ext import ndb

from ndb_util import FancyModel
from sharded_counter import ShardedCounter
from unique_tasks import add_task_once_in_current_interval

IS_PUBLIC_ENVIRONMENT = os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine')


class Level(FancyModel):
    name_ish = ndb.StringProperty(required=True)
    start_time = ndb.DateTimeProperty(auto_now_add=True)
    end_time = ndb.DateTimeProperty()
    star_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    garbage_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    updated_timestamp = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def create(cls, name_ish):
        star_votes_counter = ShardedCounter.create(20)
        garbage_votes_counter = ShardedCounter.create(20)
        level = cls()
        level.star_votes_counter_key = star_votes_counter.key
        level.garbage_votes_counter_key = garbage_votes_counter.key
        level.name_ish = name_ish
        level.put()
        return level

    def _to_client_model_shared(self):
        excludes = [
            'star_votes_counter_key',
            'garbage_votes_counter_key'
        ]
        return self.to_dict(exclude=excludes)

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

    @classmethod
    def get_singleton(cls):
        return cls.get_or_insert('singleton')


def set_current_level(level):
    cur_level = CurrentLevel.get_singleton()
    if level is None:
        cur_level.level_key = None
    else:
        cur_level.level_key = level.key
    cur_level.put()


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
        return ndb.Key(UserVote, user_id, parent=level_key)


def get_current_vote(user_id):
    cur_level = get_current_level()
    if cur_level is None:
        return None
    return UserVote.get_key(user_id, cur_level.key).get()


app = Flask(__name__)


@app.route('/api/config')
def handle_get_config():
    return jsonify({
        'login_url': users.create_login_url('/admin/'),
        'logout_url': users.create_logout_url('/')
    })


@app.route('/api/level/current')
def handle_get_current_level():
    cur_level = get_current_level()
    if cur_level is None:
        return jsonify(None)
    return jsonify(cur_level.to_client_model_fast())


@app.route('/api/vote/<user_id>')
def handle_get_current_vote(user_id):
    cur_vote = get_current_vote(user_id)
    if cur_vote is not None:
        cur_vote = cur_vote.to_dict()
    return jsonify(cur_vote)


class CommitVoteResult(object):
    def __init__(self, flask_response, counts_need_update=False):
        self.flask_response = flask_response
        self.counts_need_update = counts_need_update


@ndb.transactional(xg=True)
def commit_vote(user_id, choice, level_key):
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
    prior_vote = get_current_vote(user_id)
    if prior_vote is not None:
        prior_vote_choice = prior_vote.choice
        if prior_vote_choice == choice:
            return CommitVoteResult(jsonify(prior_vote.to_dict()))
        new_vote = prior_vote
    else:
        prior_vote_choice = None
        new_vote = UserVote.create(user_id, level_key)
    new_vote.choice = choice
    new_vote.put()
    if choice == 'star':
        cur_level.star_votes_counter_key.get().increment()
    elif choice == 'garbage':
        cur_level.garbage_votes_counter_key.get().increment()
    else:
        raise AssertionError('Should not be possible to reach here with invalid choice {}'.format(choice))
    if prior_vote_choice == 'star':
        cur_level.star_votes_counter_key.get().decrement()
    elif prior_vote_choice == 'garbage':
        cur_level.garbage_votes_counter_key.get().decrement()
    counts_need_update = True
    return CommitVoteResult(handle_get_current_vote(user_id), True)


@app.route('/api/vote', methods=['POST'])
def handle_vote():
    logging.debug('DOING THE OTHER THING')
    user_id = request.form['user_id']
    if not user_id:
        return 'Missing user_id', 400
    choice = request.form['choice']
    if not choice:
        return 'Missing choice', 400
    urlsafe_level_key = request.form['level_key']
    if not urlsafe_level_key:
        return 'Missing level_key', 400
    level_key = ndb.Key(urlsafe=urlsafe_level_key)
    commit_vote_result = commit_vote(user_id, choice, level_key)
    if commit_vote_result.counts_need_update:
        try:
            refresh_interval_seconds = 5
            add_task_once_in_current_interval(
                base_name = 'update-and-broadcast-level-counts-task',
                interval_seconds = refresh_interval_seconds,
                queue_name = 'update-and-broadcast-level-counts-queue',
                url = '/api/admin/update-and-broadcast-level-counts',
                params = {'level_key': urlsafe_level_key},
                eta = datetime.datetime.utcnow() + datetime.timedelta(seconds=refresh_interval_seconds)
            )
        except Exception:
            # Caller doesn't need to know what went wrong in here:
            logging.exception('Error while adding update count task')
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


@app.route('/api/admin/update-and-broadcast-level-counts', methods=['POST'])
def handle_update_level_counts():
    urlsafe_level_key = request.form['level_key']
    if not urlsafe_level_key:
        return 'Missing level_key', 400
    level_key = ndb.Key(urlsafe=urlsafe_level_key)
    level = level_key.get()
    if not level:
        return 'Couldn\'t find level for given key', 400
    updated_level = level.to_client_model_exact()

    pubsub_emulator_host = os.environ.get('PUBSUB_EMULATOR_HOST', '')
    if pubsub_emulator_host:
        publish_base_url = 'http://' + pubsub_emulator_host
        validate_certificate = False
    else:
        publish_base_url = 'https://pubsub.googleapis.com'
        validate_certificate = True
    publish_url = '{}/v1/projects/{}/topics/{}:publish'.format(
        publish_base_url,
        app_identity.get_application_id(),
        'level-updates-topic'
    )
    auth_token, _ = app_identity.get_access_token([
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/pubsub'
    ])
    post_body = {
        'messages': [
            { 'data': updated_level }
        ]
    }
    post_body_string = flask.json.dumps(post_body)
    publish_response = urlfetch.fetch(
        publish_url,
        deadline=5, # seconds
        method=urlfetch.POST,
        payload=post_body_string,
        headers={
            'Authorization': 'Bearer {}'.format(auth_token),
            'Content-Type': 'application/json'
        },
        validate_certificate=validate_certificate
    )
    if (not publish_response) or publish_response.status_code != 200:
        error_message = 'HTTP {} returned from POST to {}\n response={}'.format(
            publish_response.status_code,
            publish_url,
            repr(publish_response.__dict__)
        )
        raise Exception(error_message)
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

