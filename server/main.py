import datetime
import logging

from flask import Flask, jsonify, request
from google.appengine.api import users
from google.appengine.ext import ndb

from sharded_counter import ShardedCounter

class Level(ndb.Model):
    name_ish = ndb.StringProperty(required=True)
    start_time = ndb.DateTimeProperty(auto_now_add=True)
    end_time = ndb.DateTimeProperty()
    star_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    star_votes_final_count = ndb.IntegerProperty()
    garbage_votes_counter_key = ndb.KeyProperty(kind=ShardedCounter)
    garbage_votes_final_count = ndb.IntegerProperty()

    @classmethod
    def create(cls):
        star_votes_counter = ShardedCounter()
        star_votes_counter_key = star_votes_counter.put()
        garbage_votes_counter = ShardedCounter()
        garbage_votes_counter_key = star_votes_counter.put()
        level = cls()
        level.star_votes_counter_key = star_votes_counter_key
        level.garbage_votes_counter_key = garbage_votes_counter_key
        level.put()


class CurrentLevel(ndb.Model):
    level_key = ndb.KeyProperty()

    @classmethod
    def get_singleton(cls):
        return cls.get_or_insert('singleton')


def set_current_level(level):
    cur_level = CurrentLevel.get_singleton()
    cur_level.level_key = level.key
    cur_level.put()


def get_current_level():
    cur_level_key =  CurrentLevel.get_singleton().level_key
    if cur_level_key is None:
        return None
    return cur_level_key.get()


class UserVote(ndb.Model):
    user_id = ndb.StringProperty()
    level_key = ndb.KeyProperty()
    vote_choice = ndb.StringProperty(choices=['star', 'garbage'])


def get_current_vote(user_id):
    cur_level = get_current_level()
    if cur_level is None:
        return None
    vote = UserVote.query(UserVote.user_id == user_id, UserVote.level_key == cur_level.key)


app = Flask(__name__)


@app.route('/api/config', methods=['GET'])
def handle_get_admin_config():
    return jsonify({
        'login_url': users.create_login_url('/admin'),
        'logout_url': users.create_logout_url('/admin')
    })


@app.route('/api/admin/start-new-level', methods=['POST'])
def handle_start_new_level():
    new_level = Level()
    new_level.name_ish = request.form['name_ish']
    new_level.put()
    set_current_level(new_level)


@app.route('/api/admin/end-current-level', methods=['POST'])
def handle_end_current_level():
    cur_level = get_current_level()
    if cur_level is not None:
        cur_level.end_time = datetime.datetime.now()
    set_current_level(None)


@app.route('/api/level/current')
def handle_get_current_level():
    cur = get_current_level()
    if cur is not None:
        cur = cur.to_dict()
    return jsonify(cur)


@app.route('/api/vote/<user_id>')
def handle_get_current_vote(user_id):
    return jsonify(get_current_vote(user_id))


@app.route('/api/vote', methods=['POST'])
def handle_vote():
    # TODO check level_id is current
    # check if user already voted, if so we must inc / dec existing counters
    user_id = request.form['user_id']
    choice = request.form['choice']
    level_id = request.form['level_id']
    

@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500

