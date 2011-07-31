import ConfigParser
import math


class ConfigBag(object):
    def __init__(self, data):
        self.__dict__.update(data)

def orderwise_singularize(data):
    memo = set()
    results = []
    for item in data:
        if item not in memo:
            memo.add(item)
            results.append(item)
    return results

def get_configs(config_file):
    parser = ConfigParser.SafeConfigParser()
    parser.read([config_file])

    main = dict(parser.items("main"))
    instances = []
    roomsets = []
    roompeers = {}

    for section in parser.sections():
        if section == 'main':
            continue
        inst = dict(parser.items(section))
        inst['name'] = section
        inst['port'] = int(inst['port'])
        inst['addr'] = (inst['host'], inst['port'])
        instances.append(inst)
    instances.sort(key=lambda i: i['addr'])

    mask = int(math.ceil(math.log(len(instances), 2)))

    for i, inst in enumerate(instances):
        inst['mask'] = mask
        inst['value'] = i
        inst['peers'] = [n['addr'] for j, n in enumerate(instances) if i != j]
        roomsets.append(inst['roomset'])
        roompeers.setdefault(inst['roomset'], []).append(i)

    main['roomsets'] = orderwise_singularize(roomsets)
    main['roompeers'] = roompeers
    main['instances'] = map(ConfigBag, instances)
    main = ConfigBag(main)

    return main

def rid(conf, roomname, username):
    roomset = conf.roomsets[hash(roomname) % len(conf.roomsets)]
    peers = conf.roompeers[roomset]
    return peers[hash(username) % len(peers)]
