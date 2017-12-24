import datetime
import logging

from flask import Flask, jsonify, request
from google.appengine.api import users
from google.appengine.ext import ndb

from ndb_util import FancyModel
from sharded_counter import ShardedCounter

class Level(FancyModel):
    name_ish = ndb.StringProperty(required=True)
    start_time = ndb.DateTimeProperty(auto_now_add=True)
    end_time = ndb.DateTimeProperty()
    star_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    star_votes_final_count = ndb.IntegerProperty()
    garbage_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    garbage_votes_final_count = ndb.IntegerProperty()

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


@app.route('/api/admin/start-new-level', methods=['POST'])
def handle_start_new_level():
    finish_current_level()
    new_level = Level.create(request.form['name_ish'])
    set_current_level(new_level)
    return ('', 204)


@app.route('/api/admin/end-current-level', methods=['POST'])
def handle_end_current_level():
    finish_current_level()
    set_current_level(None)
    return ('', 204)


@app.route('/api/level/current')
def handle_get_current_level():
    cur_level = get_current_level()
    if cur_level is None:
        return jsonify(None)
    excludes = [
        'star_votes_counter_key',
        'garbage_votes_counter_key'
    ]
    cur_level_dict = cur_level.to_dict(exclude=excludes)
    cur_level_dict['star_votes_count'] = cur_level.star_votes_counter_key.get().get_count_fast()
    cur_level_dict['garbage_votes_count'] = cur_level.garbage_votes_counter_key.get().get_count_fast()
    cur_level_dict['key'] = cur_level.key.urlsafe()
    return jsonify(cur_level_dict)


@app.route('/api/vote/<user_id>')
def handle_get_current_vote(user_id):
    cur_vote = get_current_vote(user_id)
    if cur_vote is not None:
        cur_vote = cur_vote.to_dict()
    return jsonify(cur_vote)


@app.route('/api/vote', methods=['POST'])
def handle_vote():
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

    @ndb.transactional(xg=True)
    def commit_vote():
        # confirm level id is current
        cur_level = get_current_level()
        if cur_level is None:
            return 'No current level to vote on', 400
        if cur_level.key != level_key:
            return 'Cannot vote on level {} as it is not the current level ({})'.format(level_key.urlsafe(), cur_level.key.urlsafe()), 400
        prior_vote = get_current_vote(user_id)
        if prior_vote is not None:
            prior_vote_choice = prior_vote.choice
            if prior_vote_choice == choice:
                return jsonify(prior_vote.to_dict())
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
        return handle_get_current_vote(user_id)
    return commit_vote()
    

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

