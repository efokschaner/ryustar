import datetime
import hashlib
import time

from google.appengine.api import taskqueue

def _get_interval_number(dt, interval_seconds):
    """Returns the number of the current interval.

    Args:
        dt: The datetime to convert
        interval_seconds: The length of the interval
    Returns:
        int: Interval number.
    """
    return int(time.mktime(dt.timetuple()) / interval_seconds)


def add_task_once_in_current_interval(base_name, interval_seconds, **kwargs):
    """Enqueues the given Task only if a task with the same name
        does not already exist in the current time "interval"

    Args:
        base_name:
            tasks with the same base_name will be deduplicated against each other
            tasks with a different base_name can run in the same interval
        interval_seconds:
            The duration of the time interval in which the task shoud be unique.
        kwargs:
            Forwarded as kwargs to google.appengine.api.taskqueue.add(...)
            See https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.taskqueue#google.appengine.api.taskqueue.add
            'name' kwarg will NOT be honored as it is the mechanism of uniqueness
    """
    interval_num = _get_interval_number(datetime.datetime.utcnow(), interval_seconds)
    # https://cloud.google.com/appengine/docs/standard/java/taskqueue/push/creating-tasks#naming_a_task
    # Recommends spreading task names across keyspace using a hash.
    unhashed_task_name = '{}{}{}'.format(base_name, interval_seconds, interval_num)
    name_hash = hashlib.sha1()
    name_hash.update(unhashed_task_name)
    kwargs['name'] = name_hash.hexdigest()
    try:
        taskqueue.add(**kwargs)
    except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
        pass
