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

class LocalData(object):
    __slots__ = ['local_storage', 'initial_contents']

    @property
    def underlying(self):
        try:
            return self.local_storage.underlying
        except AttributeError:
            self.underlying = copy(self.initial_contents)
            return self.underlying
    @underlying.setter
    def underlying(self, value):
        try:
            self.local_storage.underlying = value
        except AttributeError:
            self.local_storage = local()
            self.underlying = value
    @underlying.deleter
    def underlying(self):
        del self.local_storage.underlying


class LocalList(LocalData, MutableSequence):
    """A mutable sequence object with thread-local contents"""
    __slots__ = ['local_storage', 'initial_contents']

    def __init__(self, iterable=()):
        self.initial_contents = list(iterable)

    def __getitem__(self, key):
        return self.underlying[key]
    def __setitem__(self, key, value):
        self.underlying[key] = value
    def __delitem__(self, key):
        del self.underlying[key]
    def __len__(self):
        return len(self.underlying)
    def insert(self, index, object):
        self.underlying.insert(index, object)


class LocalDict(LocalData, MutableMapping):
    """A mutable mapping object with thread-local contents"""
    __slots__ = ['local_storage', 'initial_contents']

    def __init__(self, *args, **kwargs):
        self.initial_contents = dict(*args, **kwargs)

    def __getitem__(self, key):
        return self.underlying[key]
    def __setitem__(self, key, value):
        self.underlying[key] = value
    def __delitem__(self, key):
        del self.underlying[key]
    def __iter__(self):
        return iter(self.underlying)
    def __len__(self):
        return len(self.underlying)


__all__ = ['LocalList', 'LocalDict']
