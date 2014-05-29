from collections import Mapping
from noconflict import classmaker
from copy import copy, deepcopy

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
        if name not in getattr_static(obj, '__slots__'):
            raise AttributeError('%s cannot have attribute %s' \
                                 % (repr(type(obj).__name__),
                                    repr(name)))
        attr_descriptor = getattr_static(obj, name)
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
        normal_cls = type(name, bases, namespace)
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

        namespace = dict(namespace)
        namespace['__setattr__'] = __setattr__
        namespace['__delattr__'] = __delattr__
        # python name munging changes __immutable to this
        namespace['_ImmutableEnforcerMeta__immutable'] = False
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

__all__ = ['ImmutableEnforcerMeta', 'ImmutableDict', 'FrozenDict']
