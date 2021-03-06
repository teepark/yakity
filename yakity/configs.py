import ConfigParser
import math
import random


class ConfigBag(object):
    def __init__(self, data):
        self.__dict__.update(data)

def orderwise_singularize(data):
    memo = set()
    results = []
    for subset in data:
        for item in subset:
            if item not in memo:
                memo.add(item)
                results.append(item)
    return results

def get_configs(config_file):
    parser = ConfigParser.SafeConfigParser()
    parser.read([config_file])

    main = dict(parser.items("main"))
    instances = []
    roomsets = []  # ordered list of all roomsets
    roompeers = {} # roomset -> list of RIDs

    for section in parser.sections():
        if section == 'main':
            continue
        inst = dict(parser.items(section))
        inst['name'] = section
        inst['port'] = int(inst['port'])
        inst['roomsets'] = filter(None, inst['roomsets'].split(','))
        inst['addr'] = (inst['host'], inst['port'])
        instances.append(inst)
    instances.sort(key=lambda i: i['addr'])

    mask = (1 << int(math.ceil(math.log(len(instances), 2)))) - 1

    for i, inst in enumerate(instances):
        inst['mask'] = mask
        inst['value'] = i
        inst['peers'] = [n['addr'] for j, n in enumerate(instances) if i != j]
        roomsets.append(inst['roomsets'])
        for roomset in inst['roomsets']:
            roompeers.setdefault(roomset, []).append(i)

    roomsets = orderwise_singularize(roomsets)

    for inst in instances:
        inst['pubmask'] = (1 << int(math.ceil(math.log(len(roomsets), 2)))) - 1

    # roomset -> broadcast RID
    roombroadcast = dict((rs, i) for i, rs in enumerate(roomsets))

    for inst in instances:
        inst['pubvals'] = [roombroadcast[r] for r in inst['roomsets']]

    main['roomsets'] = roomsets
    main['roompeers'] = roompeers
    main['roombroadcast'] = roombroadcast
    main['instances'] = map(ConfigBag, instances)
    main = ConfigBag(main)

    return main

def roomset(conf, roomname):
    return conf.roomsets[hash(roomname) % len(conf.roomsets)]

def rids(conf, roomset, username=None):
    result = conf.roompeers[roomset][:]
    if username is not None:
        preferred = result[hash(username) % len(result)]
        result.remove(preferred)
        result = [preferred] + result
    return result

def pub_rid(conf, roomname):
    return conf.roombroadcast[roomset(conf, roomname)]
