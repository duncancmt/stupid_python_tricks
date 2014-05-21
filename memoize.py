import decorator
import warnings
from weakref import WeakKeyDictionary
from weakcompoundkey import WeakCompoundKey
from collections import MutableMapping, Callable
from threading import RLock
from itertools import imap

def decorator_apply(dec, func, args, kwargs):
    """
    Decorate a function by preserving the signature even if dec
    is not a signature-preserving decorator.
    """
    return decorator.FunctionMaker.create(
        func, 'return decorated(%(signature)s)',
        dict(decorated=dec(func, *args, **kwargs)), __wrapped__=func)

@decorator.decorator
def decorator_decorator(dec, func, *args, **kwargs):
    """Decorator for decorators"""
    if isinstance(func, Callable):
        return decorator_apply(dec, func, args, kwargs)
    else:
        return dec(func, *args, **kwargs)

@decorator_decorator
def memoize(f, cache=None):
    """memoize memoizes its argument.
    Argument references are strongly held, which can lead to memory leaks.
    If you are concerned about this, use the lower-performance weakmemoize.
    memoize is intended for use as a decorator. e.g.

    @memoize
    def foo(*args, **kwargs):
        ...

    However, it has an alternate invocation that lets you control how the
    memoization dictionary is built.

    memo_dict = {}
    @memoize(memo_dict)
    def foo(*args, **kwargs):
        ...

    In this case, memoize will use memo_dict to store memoization information."""
    if isinstance(f, MutableMapping):
        assert cache is None
        @decorator_decorator
        def memoize_with_cache(new_f):
            return memoize(new_f, cache=f)
        return memoize_with_cache

    if cache is None:
        cache = {}

    def memoized(*args, **kwargs):
        try:
            hash(args)
            key = (args, frozenset(kwargs.iteritems()))
            hashable = True
        except TypeError as e:
            if len(e.args) == 1 and isinstance(e.args[0], basestring) and e.args[0].startswith("unhashable type:"):
                hashable = False
            else:
                raise

        if hashable:
            if key in cache:
                return cache[key]
            else:
                cache[key] = retval = f(*args, **kwargs)
                return retval
        else:
            warnings.warn("Unable to memoize: unhashable argument")
            return f(*args, **kwargs)
    return memoized

@decorator_decorator
def weakmemoize(f, cache=None):
    """weakmemoize memoizes its argument.
    Argument references are weakly held to prevent memory leaks.
    There is a substantial performance penalty to how weakmemoize holds its references.
    If you are concerned about this, use the higher-performance memoize.
    weakmemoize is intended for use as a decorator. e.g.

    @weakmemoize
    def foo(*args, **kwargs):
        ...

    However, it has an alternate invocation that lets you control how the
    memoization dictionary is built.

    memo_dict = WeakKeyDictionary()
    @weakmemoize(memo_dict)
    def foo(*args, **kwargs):
        ...

    In this case, weakmemoize will use memo_dict to store memoization information."""
    if isinstance(f, WeakKeyDictionary): # stupid python2 old-style classes
                                         # WeakKeyDictionary instances are not instances
                                         # of MutableMapping, for some asinie reason
        assert cache is None
        @decorator_decorator
        def weakmemoize_with_cache(new_f):
            return weakmemoize(new_f, cache=f)
        return weakmemoize_with_cache

    if cache is None:
        cache = WeakKeyDictionary()

    def weakmemoized(*args, **kwargs):
        try:
            key = WeakCompoundKey(*args, **kwargs)
            hashable = True
        except TypeError as e:
            if len(e.args) == 1 and isinstance(e.args[0], basestring) \
               and (e.args[0].startswith("unhashable type:") \
                    or e.args[0].startswith('cannot create weak reference to')):
                hashable = False
            else:
                raise

        if hashable:
            if key in cache:
                return cache[key]
            else:
                cache[key] = retval = f(*args, **kwargs)
                return retval
        else:
            warnings.warn("Unable to memoize: unable to hash or weak reference argument")
            return f(*args, **kwargs)
    return weakmemoized


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

    def add_new(self, key, value):
        PREV, NEXT, KEY, VALUE = 0, 1, 2, 3
        link = [None, None, key, value]
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
                    self.add_new(key, value)
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

memoized = memoize
weakmemoized = weakmemoize
__all__ = ['memoize','memoized', 'weakmemoize', 'weakmemoized']
