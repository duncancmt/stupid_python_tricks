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


from copy import copy
from threading import local
from collections import MutableSequence, MutableMapping
from proxy import BetterProxy

class LocalData(object):
    __slots__ = ['local_storage', 'prototype']
    def __init__(self, prototype):
        self.local_storage = local()
        self.prototype = prototype

    @property
    def _obj(self):
        try:
            return self.local_storage._obj
        except AttributeError:
            self.local_storage._obj = copy(self.prototype)
            return self._obj
    @_obj.setter
    def _obj(self, value):
        self.local_storage._obj = value
    @_obj.deleter
    def _obj(self):
        del self.local_storage._obj


class LocalList(LocalData, MutableSequence):
    """A mutable sequence object with thread-local contents"""
    __slots__ = ['local_storage', 'prototype']

    def __init__(self, iterable=()):
        super(LocalList, self).__init__(list(iterable))

    def __getitem__(self, key):
        return self._obj[key]
    def __setitem__(self, key, value):
        self._obj[key] = value
    def __delitem__(self, key):
        del self._obj[key]
    def __len__(self):
        return len(self._obj)
    def insert(self, index, object):
        self._obj.insert(index, object)


class LocalDict(LocalData, MutableMapping):
    """A mutable mapping object with thread-local contents"""
    __slots__ = ['local_storage', 'prototype']

    def __init__(self, *args, **kwargs):
        super(LocalDict, self).__init__(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self._obj[key]
    def __setitem__(self, key, value):
        self._obj[key] = value
    def __delitem__(self, key):
        del self._obj[key]
    def __iter__(self):
        return iter(self._obj)
    def __len__(self):
        return len(self._obj)


class LocalWrapper(LocalData, BetterProxy):
    """LocalWrapper makes an object copy itself for each thread it's accessed
    from.

    Objects are copied through the normal copy.copy mechanism. This creates
    shallow copies. All threads get a unique copy and all threads copies are
    distinct from the prototype passed to LocalWrapper.

    Mutating the prototype after passing it to LocalWrapper results in strange
    behavior. Don't do it. If you have to mutate the original object, doing
    something like LocalWrapper(copy.copy(prototype)) will be much safer.
    """
    local_storage = None
    prototype = None


__all__ = ['LocalList', 'LocalDict', 'LocalWrapper']
