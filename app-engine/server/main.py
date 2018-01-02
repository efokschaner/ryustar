import datetime
import logging
import os

from flask import Flask, jsonify, request

from google.appengine.api import users, taskqueue
from google.appengine.ext import ndb

import config
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
    pubsub.schedule_push_current_level()


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
        return ndb.Key(UserVote, '{}-{}'.format(level_key.urlsafe(), user_id))


def get_current_vote(user_id):
    cur_level = get_current_level()
    if cur_level is None:
        return None
    return UserVote.get_key(user_id, cur_level.key).get()


app = Flask(__name__)


@app.route('/api/config')
def handle_get_config():
    conf = config.PersistentConfig.get_singleton()
    client_conf = conf.to_client_model()
    client_conf['login_url'] = users.create_login_url('/admin/')
    client_conf['logout_url'] = users.create_logout_url('/')
    return jsonify(client_conf)


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
        pubsub.schedule_push_current_level()
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
    cur_level = get_current_level()
    if cur_level is None:
        cur_level_dict = None
    else:
        cur_level_dict = cur_level.to_client_model_exact()
    pubsub.publish('level-updates-topic', cur_level_dict)
    return ('', 200)


@app.route('/api/admin/increase-current-level-total-counter-shards', methods=['POST'])
def handle_increase_current_level_total_counter_shards():
    total_shards = request.form['total_shards']
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

