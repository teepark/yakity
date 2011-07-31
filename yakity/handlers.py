from __future__ import absolute_import

from . import rooms, configs


roomage = {}
joinage = {}

ROOM_HIST_DEPTH = 32
WAIT_TIMEOUT = 30.0


def get_room(name):
    if name not in roomage:
        roomage[name] = rooms.Room(ROOM_HIST_DEPTH)
    return roomage[name]


def _join(roomname, username):
    room = get_room(roomname)
    joinage.setdefault(roomname, set()).add(username)
    return room.add({'event': 'join', 'user': username})

def _depart(roomname, username):
    room = get_room(roomname)
    if roomname not in joinage or username not in joinage[roomname]:
        return 0

    joinage[roomname].remove(username)
    if not joinage[roomname]:
        joinage.pop(roomname)
        roomage.pop(roomname)

    return room.add({'event': 'depart', 'user': username})

def _say(roomname, username, message):
    room = get_room(roomname)
    if username not in joinage[roomname]:
        return 0
    return room.add({'event': 'msg', 'user': username, 'msg': message})


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
            configs.rid(config, roomname, username),
            (node.addr, roomname, username), {})
    return _join(roomname, username)

def depart(node, config, roomname, username):
    node.publish(config.service, "peer_depart",
            configs.rid(config, roomname, username),
            (node.addr, roomname, username), {})
    return _depart(roomname, username)

def say(node, config, roomname, username, message):
    node.publish(config.service, "peer_say",
            configs.rid(config, roomname, username),
            (node.addr, roomname, username, message), {})
    return _say(roomname, username, message)

def wait(node, config, roomname, last_seen):
    return get_room(roomname).wait(last_seen, WAIT_TIMEOUT)
