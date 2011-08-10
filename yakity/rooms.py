import collections
import time

import greenhouse


class Room(object):
    def __init__(self, history_depth=16):
        self._depth = history_depth
        self._data = collections.deque(maxlen=history_depth)
        self._total = 0
        self._wait = greenhouse.Event()

    def add(self, item):
        self._total += 1
        self._data.append(item)
        self._wait.set()
        self._wait.clear()
        item['counter'] = self._total
        item['timestamp'] = time.mktime(time.gmtime())
        return self._total

    def since(self, count):
        index = max(0, count - max(0, self._total - self._depth))
        return list(self._data)[index:]

    def wait(self, count, timeout=None):
        if count == self._total and self._wait.wait(timeout):
            return []

        return self.since(count)
