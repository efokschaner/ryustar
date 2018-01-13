import random

from google.appengine.api import memcache
from google.appengine.ext import ndb

from ndb_util import FancyModel

class _CounterShard(FancyModel):
    """Shards for each named counter."""
    count = ndb.IntegerProperty(default=0)


class ShardedCounter(FancyModel):
    num_shards = ndb.IntegerProperty(default=0)

    @classmethod
    def create(cls, num_shards):
        counter = cls()
        counter.increase_total_shards(num_shards)
        counter.put()
        return counter

    def increase_total_shards(self, num_total_shards):
        self.num_shards = max(self.num_shards, num_total_shards)
        self.put()

    def get_count_fast(self):
        total = memcache.get(self._get_memcache_key())
        if total is None:
            total = self.get_count_exact()
        return total

    def get_count_exact(self):
        total = 0
        for shard in ndb.get_multi(self._get_all_keys()):
            if shard is not None:
                total += shard.count
        memcache.add(self._get_memcache_key(), total, 120)
        return total

    @ndb.transactional
    def increment(self):
        shard = _CounterShard.get_or_insert(self._get_random_shard_key_name())
        shard.count += 1
        shard.put()
        # Memcache increment does nothing if the name is not a key in memcache
        ndb.get_context().call_on_commit(lambda: memcache.incr(self._get_memcache_key()))

    @ndb.transactional
    def decrement(self):
        shard = _CounterShard.get_or_insert(self._get_random_shard_key_name())
        shard.count -= 1
        shard.put()
        # Memcache decrement does nothing if the name is not a key in memcache
        ndb.get_context().call_on_commit(lambda: memcache.decr(self._get_memcache_key()))

    def _get_memcache_key(self):
        return 'ShardedCounter-{}'.format(self.key.id())

    def _get_shard_key_name(self, index):
        return '{}-{}'.format(self.key.id(), index)

    def _get_shard_key(self, index):
        return ndb.Key(_CounterShard, self._get_shard_key_name(index))

    def _get_random_shard_key_name(self):
        random_index = random.randint(0, self.num_shards - 1)
        return self._get_shard_key_name(random_index)

    def _get_all_keys(self):
        return [self._get_shard_key(i) for i in xrange(0, self.num_shards)]
