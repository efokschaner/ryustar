import base64
import datetime
import logging
import os

import flask.json

from google.appengine.api import app_identity, urlfetch

from unique_tasks import add_task_once_in_current_interval


def schedule_publish_endpoint(url):
    try:
        refresh_interval_seconds = 5
        add_task_once_in_current_interval(
            base_name = url,
            interval_seconds = refresh_interval_seconds,
            queue_name = 'publish-endpoint-queue',
            url = '/api/admin/publish-endpoint',
            params = {'url': url},
            eta = datetime.datetime.utcnow() + datetime.timedelta(seconds=refresh_interval_seconds)
        )
    except Exception:
        # Caller doesn't need to know what went wrong in here:
        logging.exception('Error while adding publish task')


def publish(topic_name, message_data_object):
    pubsub_emulator_host = os.environ.get('PUBSUB_EMULATOR_HOST')
    if pubsub_emulator_host:
        publish_base_url = 'http://' + pubsub_emulator_host
        validate_certificate = False
    else:
        publish_base_url = 'https://pubsub.googleapis.com'
        validate_certificate = True
    publish_url = '{}/v1/projects/{}/topics/{}:publish'.format(
        publish_base_url,
        app_identity.get_application_id(),
        topic_name
    )
    auth_token, _ = app_identity.get_access_token([
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/pubsub'
    ])
    message_data_string = base64.b64encode(unicode(flask.json.dumps(message_data_object), 'utf-8'))
    post_body = {
        'messages': [
            { 'data': message_data_string }
        ]
    }
    post_body_string = flask.json.dumps(post_body)
    publish_response = urlfetch.fetch(
        publish_url,
        deadline=10, # seconds
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
