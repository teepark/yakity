from __future__ import absolute_import

import functools

from . import rooms, configs


roomage = {}
joinage = {}

ROOM_HIST_DEPTH = 32
WAIT_TIMEOUT = 30.0


def register(node, config, instance_config):
    for name, handler, schedule in [
            ('join', join, False),
            ('depart', depart, False),
            ('say', say, False),
            ('wait', wait, True)]:
        node.accept_rpc(
                config.service,
                name,
                instance_config.mask,
                instance_config.value,
                functools.partial(handler, node, config),
                schedule=schedule)

    for name, handler in [
            ('peer_join', peer_join),
            ('peer_depart', peer_depart),
            ('peer_say', peer_say)]:
        for pubval in instance_config.pubvals:
            node.accept_publish(
                    config.service,
                    name,
                    instance_config.mask,
                    pubval,
                    functools.partial(handler, node),
                    schedule=False)


def get_room(name):
    if name not in roomage:
        roomage[name] = rooms.Room(ROOM_HIST_DEPTH)
    return roomage[name]


def _join(roomname, username):
    room = get_room(roomname)

    if username in joinage.get(roomname, ()):
        return 0
    joinage.setdefault(roomname, set()).add(username)

    return room.add({'event': 'join', 'username': username})

def _depart(roomname, username):
    room = get_room(roomname)
    if roomname not in joinage or username not in joinage[roomname]:
        return 0

    result = room.add({'event': 'depart', 'username': username})

    joinage[roomname].remove(username)
    if not joinage[roomname]:
        joinage.pop(roomname)
        roomage.pop(roomname)
        room.add({'event': 'destruction'})

    return result

def _say(roomname, username, message):
    room = get_room(roomname)

    if username not in joinage.get(roomname, ()):
        return 0

    return room.add({'event': 'msg', 'username': username, 'msg': message})


def peer_join(node, from_addr, roomname, username):
    if node.addr != from_addr:
        _join(roomname, username)

def peer_depart(node, from_addr, roomname, username):
    if node.addr != from_addr:
        _depart(roomname, username)

def peer_say(node, from_addr, roomname, username, message):
    if node.addr != from_addr:
        _say(roomname, username, message)


def join(node, config, roomname, username):
    node.publish(config.service, "peer_join",
            configs.pub_rid(config, roomname),
            (node.addr, roomname, username), {})
    return _join(roomname, username)

def depart(node, config, roomname, username):
    node.publish(config.service, "peer_depart",
            configs.pub_rid(config, roomname),
            (node.addr, roomname, username), {})
    return _depart(roomname, username)

def say(node, config, roomname, username, message):
    node.publish(config.service, "peer_say",
            configs.pub_rid(config, roomname),
            (node.addr, roomname, username, message), {})
    return _say(roomname, username, message)

def wait(node, config, roomname, last_seen):
    return get_room(roomname).wait(last_seen, WAIT_TIMEOUT)
