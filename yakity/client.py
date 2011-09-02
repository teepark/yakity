from __future__ import absolute_import

import collections
import random

import junction
import junction.errors
from . import configs


UNSPECIFIED = object()


def prepare_client(conf, room_hint=None, user_hint=None):
    peers = [peer.addr for peer in conf.instances]
    random.shuffle(peers)

    if room_hint is not None:
        # shuffle the peers hosting the relevant room to the top of the list
        roomset = conf.roomsets[hash(room_hint) % len(conf.roomsets)]
        roomset = set(conf.roompeers[roomset])
        l1, l2 = [], []
        for i, peer in enumerate(peers):
            (l1 if i in roomset else l2).append(peer)
        peers = l1 + l2

        # shuffle the peer that should serve this username further up
        if user_hint is not None:
            rid = configs.rpc_rid(conf, room_hint, user_hint)
            peer = conf.instances[rid].addr
            peers.remove(peer)
            peers = [peer] + peers

    client = junction.Client(peers)
    client.connect()
    while client.wait_on_connections():
        client.reset()
        client.connect()
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

    def _rpc(self, method, roomname, args, kwargs, timeout):
        for rid in configs.rpc_rids(self._config, roomname):
            try:
                result = self._client.rpc(
                        self._config.service,
                        method,
                        rid,
                        args,
                        kwargs,
                        timeout)[0]
            except junction.errors.Unroutable:
                continue

            if isinstance(result, Exception):
                raise result
            if result:
                return result
            raise YakityError(method)

        raise junction.errors.Unroutable()

    def _rid(self, roomname):
        rid = self._rid_affinity.get(roomname)
        if rid is None:
            if self._username is None:
                rid = configs.rpc_rid(self._config, roomname)
            else:
                rid = configs.rpc_rid(self._config, roomname, self._username)
            self._rid_affinity[roomname] = rid
        return rid

    def join(self, roomname):
        self._rpc('join', roomname, (roomname, self._username), {},
                self._write_timeout)

    def depart(self, roomname):
        self._rpc('depart', roomname, (roomname, self._username), {},
                self._write_timeout)

    def say(self, roomname, message):
        self._rpc('say', roomname, (roomname, self._username, message), {},
                self._write_timeout)

    def read(self, roomname, last_seen, timeout=UNSPECIFIED):
        if timeout is UNSPECIFIED:
            timeout = self._wait_timeout

        return self._rpc('wait', roomname, (roomname, last_seen), {}, timeout)

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
