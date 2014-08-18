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
from weakref import WeakKeyDictionary
from weakcompoundkey import WeakCompoundKey
from collections import MutableMapping
from threading import RLock

from decorator_decorator import decorator_decorator

@decorator_decorator
def memoize(f, cache=None):
    """memoize memoizes its argument.
    Argument references are strongly held, which can lead to memory leaks.
    If you are concerned about this, use the lower-performance weakmemoize.
    memoize hooks recursions so that you won't overflow the python stack.
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
    pending = []
    lock = RLock()
    class RecursionException(BaseException):
        pass

    def memoized(*args, **kwargs):
        try:
            hash(args)
        except TypeError as e:
            if len(e.args) == 1 and isinstance(e.args[0], basestring) and e.args[0].startswith("unhashable type:"):
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
                with lock:
                    if pending:
                        raise RecursionException(key)
                    pending.append(key)
                    while pending:
                        key = pending[-1]
                        if key in cache:
                            pending.pop()
                            return cache[key]
                        else:
                            args, kwargs = key
                            try:
                                cache[key] = retval = f(*args, **dict(kwargs))
                            except RecursionException as e:
                                assert len(e.args) == 1
                                pending.append(e.args[0])
                            else:
                                pending.pop()
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
    weakmemoize hooks recursions so that you won't overflow the python stack.
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
    pending = []
    lock = RLock()
    class RecursionException(BaseException):
        pass

    def weakmemoized(*args, **kwargs):
        try:
            key = WeakCompoundKey(*args, **kwargs)
        except TypeError as e:
            if len(e.args) == 1 and isinstance(e.args[0], basestring) \
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
                with lock:
                    if pending:
                        raise RecursionException(key)
                    pending.append(key)
                    while pending:
                        key = pending[-1]
                        if key in cache:
                            pending.pop()
                            return cache[key]
                        else:
                            args, kwargs = key
                            try:
                                cache[key] = retval = f(*args, **dict(kwargs))
                            except RecursionException as e:
                                assert len(e.args) == 1
                                pending.append(e.args[0])
                            else:
                                pending.pop()
                    return retval

        else:
            warnings.warn("Unable to memoize: unable to hash or weak reference argument")
            return f(*args, **kwargs)
    return weakmemoized


memoized = memoize
weakmemoized = weakmemoize
__all__ = ['memoize','memoized', 'weakmemoize', 'weakmemoized']

import callable_module
callable_module(memoize)
