from __future__ import absolute_import

import functools

from . import handlers


def register(node, config, instance_config):
    for name, handler, schedule in [
            ('join', handlers.join, False),
            ('depart', handlers.depart, False),
            ('say', handlers.say, False),
            ('wait', handlers.wait, True)]:
        node.accept_rpc(
                config.service,
                name,
                instance_config.mask,
                instance_config.value,
                functools.partial(handler, node, config),
                schedule=schedule)

    for name, handler in [
            ('peer_join', handlers.peer_join),
            ('peer_depart', handlers.peer_depart),
            ('peer_say', handlers.peer_say)]:
        node.accept_publish(
                config.service,
                name,
                instance_config.mask,
                instance_config.value,
                functools.partial(handler, node),
                schedule=schedule)
