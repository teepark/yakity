from __future__ import absolute_import

import sys
import time

import greenhouse
import junction
from . import client, configs, service

signal = greenhouse.patched("signal")


def runservice(conf, instance_name):
    instance = [inst for inst in conf.instances if inst.name == instance_name]
    if not instance:
        print >> sys.stderr, "unknown shard %r" % instance_name
        return
    instance = instance[0]

    node = junction.Node(instance.addr, instance.peers)
    service.register(node, conf, instance)
    node.start()
    node.wait_on_connections()

    try:
        greenhouse.Event().wait()
    except KeyboardInterrupt:
        pass


def listen(conf, roomname, username=None):
    yak = client.Yakity(conf, client.prepare_client(
                conf, room_hint=roomname, user_hint=username), None)

    timediff = time.mktime(time.localtime()) - time.mktime(time.gmtime())

    try:
        for event in yak.stream(roomname):
            if event['event'] == 'join':
                print "[%s] * %s has joined" % (
                        time.ctime(event['timestamp'] + timediff),
                        event['username'])
            elif event['event'] == 'depart':
                print "[%s] * %s has left" % (
                        time.ctime(event['timestamp'] + timediff),
                        event['username'])
            elif event['event'] == 'msg':
                print "[%s] <%s> %s" % (
                        time.ctime(event['timestamp'] + timediff),
                        event['username'],
                        event['msg'])
            elif event['event'] == 'destruction':
                print "[%s] * ROOM CLOSED" % (
                        time.ctime(event['timestamp'] + timediff),)
                break
            else:
                raise Exception("unrecognized event: %r" % event)
    except KeyboardInterrupt:
        pass


def speak(conf, roomname, username):
    def int_handler(signum, frame):
        greenhouse.end(speaker_glet)
    signal.signal(signal.SIGINT, int_handler)

    yak = client.Yakity(conf, client.prepare_client(
        conf, room_hint=roomname, user_hint=username), username)

    finished = greenhouse.Event()

    @greenhouse.schedule
    @greenhouse.greenlet
    def speaker_glet():
        try:
            yak.join(roomname)
            print "(ctrl-c to exit)"
            while 1:
                greenhouse.stdout.write("%s> " % roomname)
                line = greenhouse.stdin.readline().rstrip()
                if line: yak.say(roomname, line)
        finally:
            yak.depart(roomname)
            finished.set()

    finished.wait()
