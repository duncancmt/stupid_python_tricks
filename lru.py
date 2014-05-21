from collections import MutableMapping
from threading import RLock
from itertools import imap

class LRUDict(MutableMapping):
    """Adapted from ActiveState recipe 578078"""
    __slots__ = ["sentinel", "root", "maxsize", "hits", "misses", "lock", "cache"]
    def __init__(self, maxsize=1024, *args, **kwargs):
        sentinel = object()
        self.sentinel = sentinel
        root = []
        root[:] = [root, root, sentinel, sentinel]
        self.root = root
        self.maxsize = maxsize
        self.hits = 0
        self.misses = 0
        self.lock = RLock()
        self.cache = {}
        self.cache.update(*args, **kwargs)

    def make_link(key, value):
        sentinel = self.sentinel
        return [ sentinel, sentinel, key, value ]

    def mark_recent_use(self, link):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            root = self.root
            link_prev, link_next, key, result = link
            link_prev[NEXT] = link_next
            link_next[PREV] = link_prev
            last = root[PREV]
            last[NEXT] = root[PREV] = link
            link[PREV] = last
            link[NEXT] = root

    def __getitem__(self, key):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            try:
                link = self.cache[key]
                self.mark_recent_use(link)
                self.hits += 1
                return link[VALUE]
            except KeyError:
                self.misses += 1
                raise

    def add_new(self, link):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            self.cache[key] = link
            root = self.root
            last = root[PREV]
            last[NEXT] = link
            link[NEXT] = root
            link[PREV] = last
            root[PREV] = link

    def replace_oldest(self, key, value):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            oldroot = self.root
            cache = self.cache
            cache[key] = oldroot
            oldroot[KEY] = key
            oldroot[VALUE] = value
            self.root = newroot = oldroot[NEXT]
            del cache[newroot[KEY]]
            sentinel = self.sentinel
            newroot[KEY] = sentinel
            newroot[VALUE] = sentinel

    def __setitem__(self, key, value):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            sentinel = self.sentinel
            link = self.cache.get(key, sentinel)
            if link is sentinel:
                maxsize = self.maxsize
                length = len(self.cache)
                if length == maxsize:
                    self.replace_oldest(key, value)
                elif length < maxsize:
                    link = self.make_link(key, value)
                    self.add_new(link)
                else:
                    raise RuntimeError("LRUDict size exceeds maximum size")
            else:
                link[VALUE] = value
                self.mark_recent_use(link)

    def remove_link(self, link):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            prev = link[PREV]
            next = link[NEXT]
            prev[NEXT] = next
            next[PREV] = prev

    def __delitem__(self, key):
        with self.lock:
            cache = self.cache
            link = cache[key]
            self.remove_link(link)
            del cache[key]

    def remove_oldest(self):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        with self.lock:
            oldroot = self.root
            newroot = oldroot[NEXT]
            last = oldroot[PREV]
            newroot[PREV] = last
            last[NEXT] = newroot
            self.root = newroot
            del self.cache[newroot[KEY]]
            sentinel = self.sentinel
            newroot[KEY] = sentinel
            newroot[VALUE] = sentinel

    def resize(self, newsize):
        _len = len
        with self.lock:
            while _len(self.cache) > newsize:
                self.remove_oldest()
            self.maxsize = newsize

    def __iter__(self):
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)

    def __repr__(self):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        return "%s.%s(%s)" % (type(self).__module__,
                              type(self).__name__,
                              repr(dict(imap(lambda (k, v): (k, v[VALUE]),
                                             self.cache.iteritems()))))


__all__ = ["LRUDict"]
