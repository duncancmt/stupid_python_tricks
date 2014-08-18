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


from collections import Mapping
from noconflict import classmaker
from copy import copy, deepcopy
from functools import wraps

from getattr_static import getattr_static

# python's built-in abc module sets these attributes on classes
ok_mutable_names = ['_abc_negative_cache', '_abc_negative_cache_version']

mro_getter = type.__dict__['__mro__'].__get__
type_dict_getter = type.__dict__['__dict__'].__get__
object_dict_getter = lambda obj: object.__getattribute__(obj, '__dict__')

def check_mutable(obj, name):
    try:
        if name in object_dict_getter(obj):
            raise AttributeError('Cannot mutate private attribute %s of %s' \
                                 % (repr(name), repr(obj)))
    except AttributeError:
        try:
            attr_descriptor = getattr_static(obj, name)
        except AttributeError:
            raise AttributeError('%s cannot have attribute %s' \
                                 % (repr(type(obj).__name__),
                                    repr(name)))
        try:
            attr_descriptor.__get__(obj, type(obj))
        except AttributeError:
            pass
        else:
            raise AttributeError('Cannot mutate private attribute %s of %s' \
                                 % (repr(name), repr(obj)))
    else:
        mro = mro_getter(type(obj))
        if mro is None:
            mro = tuple()
        for c in mro:
            if name in type_dict_getter(c):
                raise AttributeError('Cannot mutate private attribute %s of %s' \
                                     % (repr(name), repr(obj)))


class ImmutableEnforcerMeta(type):
    def __new__(mcls, name, bases, namespace):
        namespace = dict(namespace)
        # python name munging changes __immutable to this
        namespace['_ImmutableEnforcerMeta__immutable'] = False

        normal_cls = super(ImmutableEnforcerMeta, mcls).__new__(mcls, name, bases, namespace)
        fallback_setattr = getattr_static(normal_cls, '__setattr__')
        fallback_delattr = getattr_static(normal_cls, '__delattr__')

        def __setattr__(self, name, value):
            if name[0] == '_':
                check_mutable(self, name)
            fallback_setattr(self, name, value)

        def __delattr__(self, name):
            if name[0] == '_':
                check_mutable(self, name)
            fallback_delattr(self, name)

        namespace['__setattr__'] = __setattr__
        namespace['__delattr__'] = __delattr__
        immutable_cls = super(ImmutableEnforcerMeta, mcls).__new__(mcls, name, bases, namespace)
        immutable_cls.__immutable = True
        return immutable_cls


    def __setattr__(cls, name, value):
        mro_getter = type.__dict__['__mro__'].__get__
        dict_getter = type.__dict__['__dict__'].__get__
        static_setattr = type.__setattr__

        if name[0] == '_' and cls.__immutable and name not in ok_mutable_names:
            mro = mro_getter(cls)
            if mro is None:
                mro = tuple()
            for c in mro:
                if name in dict_getter(c):
                    raise AttributeError('Cannot mutate private attribute %s of %s' % (repr(name), repr(cls)))
        return static_setattr(cls, name, value)


    def __delattr__(cls, name):
        mro_getter = type.__dict__['__mro__'].__get__
        dict_getter = type.__dict__['__dict__'].__get__
        static_setattr = type.__setattr__

        if name[0] == '_' and cls.__immutable:
            mro = mro_getter(cls)
            if mro is None:
                mro = tuple()
            for c in mro:
                if name in dict_getter(c):
                    raise AttributeError('Cannot delete private attribute %s of %s' % (repr(name), repr(cls)))
        return static_setattr(cls, name, value)

class ImmutableDictBase(object):
    __metaclass__ = ImmutableEnforcerMeta
class ImmutableDict(ImmutableDictBase, Mapping):
    __metaclass__ = classmaker()
    def __init__(self, *args, **kwargs):
        self.__underlying = dict(*args, **kwargs)
    def __getitem__(self, key):
        return self.__underlying[key]
    def __iter__(self):
        return iter(self.__underlying)
    def __len__(self):
        return len(self.__underlying)
    def __hash__(self):
        try:
            return self.__hash
        except AttributeError:
            self.__hash = hash(frozenset(self.__underlying.iteritems()))
            return hash(self)
    def __repr__(self):
        return "ImmutableDict(%s)" % repr(self.__underlying)
    def __copy__(self):
        return type(self)(copy(self.__underlying))
    def __deepcopy__(self, memo):
        return type(self)(deepcopy(self.__underlying, memo))

FrozenDict = ImmutableDict


def immutableproperty(f):
    attribute_name = [None] # stupid python scoping rules
    property_name = f.func_name

    @property
    @wraps(f)
    def wrapped(self):
        # stupid python scoping rules
        if attribute_name[0] is None:
            attribute_name[0] = "_%s__%s" % (type(self).__name__,
                                             f.func_name)
        try:
            return getattr(self, attribute_name[0])
        except AttributeError:
            retval = f(self)
            setattr(self, property_name, retval)
            return retval
    @wrapped.setter
    @wraps(f)
    def wrapped(self, value):
        # stupid python scoping rules
        if attribute_name[0] is None:
            attribute_name[0] = "_%s__%s" % (type(self).__name__,
                                             f.func_name)
        setattr(self, attribute_name[0], value)

    return wrapped


__all__ = ['ImmutableEnforcerMeta', 'ImmutableDict', 'FrozenDict', 'immutableproperty']
