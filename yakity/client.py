from __future__ import absolute_import

import collections
import random

import junction
from . import configs


UNSPECIFIED = object()


def prepare_client(conf, room_hint=None, user_hint=None):
    if room_hint is None:
        peer = random.choice(conf.instances)
    else:
        if user_hint is None:
            roomset = conf.roomsets[hash(room_hint) % len(conf.roomsets)]
            peer = conf.instances[random.choice(conf.roompeers[roomset])]
        else:
            rid = configs.rpc_rid(conf, room_hint, user_hint)
            peer = conf.instances[rid]

    client = junction.Client(peer.addr)
    client.connect()
    client.wait_on_connections()
    return client

class Yakity(object):
    def __init__(self, config, junc_client, username=None,
            write_timeout=5.0, wait_timeout=None, cache_len=16):
        self._client = junc_client
        self._username = username
        self._config = config
        self._write_timeout = write_timeout
        self._wait_timeout = wait_timeout
        self._rid_affinity = {}

    def _rid(self, roomname):
        if self._username is None:
            if roomname not in self._rid_affinity:
                self._rid_affinity[roomname] = configs.rpc_rid(
                        self._config, roomname)
            return self._rid_affinity[roomname]
        return configs.rpc_rid(self._config, roomname, self._username)

    def join(self, roomname):
        result = self._client.rpc(
                self._config.service,
                'join',
                self._rid(roomname),
                (roomname, self._username),
                {},
                self._write_timeout)[0]

        if isinstance(result, Exception):
            raise result
        if not result:
            raise YakityError('join')

    def depart(self, roomname):
        result = self._client.rpc(
                self._config.service,
                'depart',
                self._rid(roomname),
                (roomname, self._username),
                {},
                self._write_timeout)[0]

        if isinstance(result, Exception):
            raise result
        if not result:
            raise YakityError('depart')

    def say(self, roomname, message):
        result = self._client.rpc(
                self._config.service,
                'say',
                self._rid(roomname),
                (roomname, self._username, message),
                {},
                self._write_timeout)[0]

        if isinstance(result, Exception):
            raise result
        if not result:
            raise YakityError('say')

    def read(self, roomname, last_seen, timeout=UNSPECIFIED):
        if timeout is UNSPECIFIED:
            timeout = self._wait_timeout

        result = self._client.rpc(
                self._config.service,
                'wait',
                self._rid(roomname),
                (roomname, last_seen),
                {},
                timeout)[0]

        if isinstance(result, Exception):
            raise result
        return result

    def stream(self, roomname):
        latest = 0
        while 1:
            result = self.read(roomname, latest, None)
            for item in result:
                yield item
                if item['event'] == 'destruction':
                    return
            if result:
                latest = result[-1]['counter']


class YakityError(Exception):
    pass
