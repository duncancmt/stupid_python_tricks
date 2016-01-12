# This file is part of stupid_python_tricks written by Duncan Townsend.
#
# stupid_python_tricks is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# stupid_python_tricks is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with stupid_python_tricks.  If not, see <http://www.gnu.org/licenses/>.


from collections import MutableMapping
from threading import RLock
from itertools import imap
from weakref import ref
from copy import deepcopy

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
        self.update(*args, **kwargs)

    def _make_link(self, key, value):
        sentinel = self.sentinel
        return [ sentinel, sentinel, key, value ]

    def _mark_recent_use(self, link):
        with self.lock:
            root = self.root
            link_prev, link_next, key, result = link
            link_prev[1] = link_next
            link_next[0] = link_prev
            last = root[0]
            last[1] = root[0] = link
            link[0] = last
            link[1] = root

    def __getitem__(self, key):
        with self.lock:
            try:
                link = self.cache[key]
                self._mark_recent_use(link)
                self.hits += 1
                return link[3]
            except KeyError:
                self.misses += 1
                raise

    def _add_new(self, link):
        with self.lock:
            self.cache[link[2]] = link
            root = self.root
            last = root[0]
            last[1] = link
            link[1] = root
            link[0] = last
            root[0] = link

    def replace_oldest(self, key, value):
        with self.lock:
            oldroot = self.root
            cache = self.cache
            cache[key] = oldroot
            oldroot[2] = key
            oldroot[3] = value
            self.root = newroot = oldroot[1]
            del cache[newroot[2]]
            sentinel = self.sentinel
            newroot[2] = sentinel
            newroot[3] = sentinel

    def __setitem__(self, key, value):
        with self.lock:
            sentinel = self.sentinel
            link = self.cache.get(key, sentinel)
            if link is sentinel:
                maxsize = self.maxsize
                length = len(self.cache)
                if length == maxsize:
                    self.replace_oldest(key, value)
                elif length < maxsize:
                    link = self._make_link(key, value)
                    self._add_new(link)
                else:
                    raise RuntimeError("LRUDict size exceeds maximum size")
            else:
                link[3] = value
                self._mark_recent_use(link)

    def _remove_link(self, link):
        with self.lock:
            prev = link[0]
            next = link[1]
            prev[1] = next
            next[0] = prev

    def __delitem__(self, key):
        with self.lock:
            cache = self.cache
            link = cache[key]
            self._remove_link(link)
            del cache[key]

    def remove_oldest(self):
        with self.lock:
            oldroot = self.root
            newroot = oldroot[1]
            last = oldroot[0]
            newroot[0] = last
            last[1] = newroot
            self.root = newroot
            del self.cache[newroot[2]]
            sentinel = self.sentinel
            newroot[2] = sentinel
            newroot[3] = sentinel

    def resize(self, newsize):
        _len = len
        with self.lock:
            while _len(self.cache) > newsize:
                self.remove_oldest()
            self.maxsize = newsize

    def __iter__(self):
        return self.cache.iterkeys()

    def __len__(self):
        return len(self.cache)

    def __repr__(self):
        return "%s.%s(%s)" % (type(self).__module__,
                              type(self).__name__,
                              repr(dict(self.iteritems())))

    def __copy__(self):
        return type(self)(self.maxsize, self.iteritems())

    def __deepcopy__(self, memo):
        return type(self)(self.maxsize,
                          imap(lambda (k,v): (deepcopy(k, memo), deepcopy(v, memo)),
                               self.iteritems()))



class IterationGuard(object):
    """
    This class taken directly from the CPython _weakrefset.py module.
    Since _weakrefset.py is not part of the standard library, we cannot
    rely on it being available.

    This context manager registers itself in the current iterators of the
    weak container, such as to delay all removals until the context manager
    exits.
    This technique should be relatively thread-safe (since sets are)."""

    def __init__(self, weakcontainer):
        # Don't create cycles
        self.weakcontainer = ref(weakcontainer)

    def __enter__(self):
        w = self.weakcontainer()
        if w is not None:
            w._iterating.add(self)
        return self

    def __exit__(self, e, t, b):
        w = self.weakcontainer()
        if w is not None:
            s = w._iterating
            s.remove(self)
            if not s:
                w._commit_removals()


class WeakKeyLRUDict(LRUDict):
    """A LRUDict that holds its references to its keys weakly.
    Patterned after weakref.WeakKeyDictionary, and much code taken from there."""
    __slots__ = LRUDict.__slots__ + ["_remove", "_pending_removals", "_iterating"]
    def __init__(self, *args, **kwargs):
        def remove(k, selfref=ref(self)):
            self = selfref()
            if self is not None:
                if self._iterating:
                    self._pending_removals.append(k)
                else:
                    try:
                        sup = super(WeakKeyLRUDict, self)
                        sup.__delitem__(k)
                    except KeyError:
                        pass
        self._remove = remove
        self._pending_removals = []
        self._iterating = set()
        super(WeakKeyLRUDict, self).__init__(*args, **kwargs)

    def _commit_removals(self):
        # NOTE: We don't need to call this method before mutating the dict,
        # because a dead weakref never compares equal to a live weakref,
        # even if they happened to refer to equal objects.
        # However, it means keys may already have been removed.
        l = self._pending_removals
        while l:
            try:
                del self[l.pop()]
            except KeyError:
                pass

    def __getitem__(self, key):
        sup = super(WeakKeyLRUDict, self)
        return sup.__getitem__(ref(key))

    def _make_link(self, key, value):
        key = ref(key, self._remove)
        sup = super(WeakKeyLRUDict, self)
        return sup._make_link(key, value)

    def replace_oldest(self, key, value):
        key = ref(key, self._remove)
        sup = super(WeakKeyLRUDict, self)
        return sup.replace_oldest(key, value)

    def __delitem__(self, key):
        key = ref(key)
        sup = super(WeakKeyLRUDict, self)
        sup.__delitem__(key)

    def __iter__(self):
        sup = super(WeakKeyLRUDict, self)
        with IterationGuard(self):
            for wr in sup.__iter__():
                obj = wr()
                if obj is not None:
                    yield obj

    def iterkeyrefs(self):
        sup = super(WeakKeyLRUDict, self)
        with IterationGuard(self):
            for wr in sup.__iter__():
                yield wr

    def keyrefs(self):
        return list(self.iterkeyrefs())

__all__ = ["LRUDict", "WeakKeyLRUDict"]
