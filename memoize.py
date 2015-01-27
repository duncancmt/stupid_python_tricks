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


import warnings
from weakref import WeakKeyDictionary, WeakValueDictionary
from weakcompoundkey import WeakCompoundKey
from collections import MutableMapping
from threading import Lock, current_thread

from decorator_decorator import decorator_decorator

@decorator_decorator
def memoize(f, cache=None):
    """memoize memoizes its argument.
    Argument references are strongly held, which can lead to memory leaks.
    If you are concerned about this, use the lower-performance weakmemoize.
    If the memoized function recurses with the same arguments, instead
    of overflowing the stack, it will deadlock.
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
    pending = WeakValueDictionary()

    def memoized(*args, **kwargs):
        try:
            hash(args)
            for a in kwargs.itervalues():
                hash(a)
        except TypeError as e:
            if len(e.args) == 1 \
                   and isinstance(e.args[0], basestring) \
                   and e.args[0].startswith("unhashable type:"):
                hashable = False
            else:
                raise
        else:
            key = (args, frozenset(kwargs.iteritems()))
            hashable = True

        if hashable:
            if key in cache:
                return cache[key]
            else:
                my_lock = Lock()
                with my_lock:
                    key_lock = pending.setdefault(key, my_lock)
                    if key_lock is my_lock:
                        # we get strange (wrong) behavior with
                        # weakrefs if we hold onto key_lock/my_lock
                        del key_lock
                        del my_lock
                        cache[key] = retval = f(*args, **kwargs)
                        return retval
                    else:
                        with key_lock:
                            return cache[key]

        else:
            warnings.warn("Unable to memoize: unhashable argument")
            return f(*args, **kwargs)
    memoized.clear = cache.clear
    return memoized

@decorator_decorator
def weakmemoize(f, cache=None):
    """weakmemoize memoizes its argument.
    Argument references are weakly held to prevent memory leaks.
    There is a substantial performance penalty to how weakmemoize holds its references.
    If you are concerned about this, use the higher-performance memoize.
    If the memoized function recurses with the same arguments, instead
    of overflowing the stack, it will deadlock.
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
    if isinstance(f, (WeakKeyDictionary, # stupid python2 old-style classes
                      MutableMapping)):  # WeakKeyDictionary instances are not instances
                                         # of MutableMapping, for some asinie reason
        assert cache is None
        @decorator_decorator
        def weakmemoize_with_cache(new_f):
            return weakmemoize(new_f, cache=f)
        return weakmemoize_with_cache

    if cache is None:
        cache = WeakKeyDictionary()
    pending = WeakValueDictionary()

    def weakmemoized(*args, **kwargs):
        try:
            key = WeakCompoundKey(*args, **kwargs)
        except TypeError as e:
            if len(e.args) == 1 \
                   and isinstance(e.args[0], basestring) \
                   and (e.args[0].startswith("unhashable type:") \
                        or e.args[0].startswith('cannot create weak reference to')):
                hashable = False
            else:
                raise
        else:
            hashable = True

        if hashable:
            if key in cache:
                return cache[key]
            else:
                my_lock = Lock()
                with my_lock:
                    # It's OK that this makes a strong reference to
                    # key. We want key to stick around at least until
                    # we leave this scope, at which point my_lock will
                    # be collected and the whole dict entry will be
                    # freed, potentially taking key with it.
                    key_lock = pending.setdefault(key, my_lock)
                    if key_lock is my_lock:
                        # we get strange (wrong) behavior with
                        # weakrefs if we hold onto key_lock/my_lock
                        del key_lock
                        del my_lock
                        cache[key] = retval = f(*args, **kwargs)
                        return retval
                    else:
                        with key_lock:
                            return cache[key]

        else:
            warnings.warn("Unable to memoize: unable to hash or weak reference argument")
            return f(*args, **kwargs)
    weakmemoized.clear = cache.clear
    return weakmemoized


memoized = memoize
weakmemoized = weakmemoize
__all__ = ['memoize','memoized', 'weakmemoize', 'weakmemoized']

import callable_module
callable_module(memoize)
