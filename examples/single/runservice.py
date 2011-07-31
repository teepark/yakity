#!/usr/bin/env python
# vim: fileencoding=utf8:et:sta:ai:sw=4:ts=4:sts=4


import greenhouse
import junction
from yakity import configs, service


conf = configs.get_configs("yakity.conf")
instance = conf.instances[0]

node = junction.Node(instance.addr, instance.peers)
service.register(node, conf, instance)
node.start()
node.wait_on_connections()

try:
    greenhouse.Event().wait()
except KeyboardInterrupt:
    pass
