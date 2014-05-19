from collections import Mapping
from noconflict import classmaker
from copy import copy, deepcopy

# python's built-in abc module sets these attributes on classes
ok_mutable_names = ['_abc_negative_cache', '_abc_negative_cache_version']

class ImmutableEnforcerMeta(type):
    def __new__(mcls, name, bases, namespace):
        old_setattr = namespace.get('__setattr__', object.__setattr__)
        old_delattr = namespace.get('__delattr__', object.__delattr__)

        mro_getter = type.__dict__['__mro__'].__get__
        type_dict_getter = type.__dict__['__dict__'].__get__
        object_dict_getter = lambda obj: object.__getattribute__(obj, '__dict__')

        def __setattr__(self, name, value):
            if name[0] == '_':
                if name in object_dict_getter(self):
                    raise AttributeError('Cannot mutate private attribute %s of %s' % (repr(name), repr(self)))
                mro = mro_getter(type(self))
                if mro is None:
                    mro = tuple()
                for c in mro:
                    if name in type_dict_getter(c):
                        raise AttributeError('Cannot mutate private attribute %s of %s' % (repr(name), repr(self)))
            return old_setattr(self, name, value)

        def __delattr__(self, name):
            if name[0] == '_':
                if name in object_dict_getter(self):
                    raise AttributeError('Cannot delete private attribute %s of %s' % (repr(name), repr(self)))
                mro = mro_getter(type(self))
                if mro is None:
                    mro = tuple()
                for c in mro:
                    if name in type_dict_getter(c):
                        raise AttributeError('Cannot delete private attribute %s of %s' % (repr(name), repr(self)))
            return old_delattr(self, name)

        namespace = dict(namespace)
        namespace['__setattr__'] = __setattr__
        namespace['__delattr__'] = __delattr__
        # python name munging changes __immutable to this
        namespace['_ImmutableEnforcerMeta__immutable'] = False
        cls = super(ImmutableEnforcerMeta, mcls).__new__(mcls, name, bases, namespace)
        cls.__immutable = True
        return cls


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
        return hash(frozenset(self.__underlying.iteritems()))
    def __repr__(self):
        return "ImmutableDict(%s)" % repr(self.__underlying)
    def __copy__(self):
        return type(self)(copy(self.__underlying))
    def __deepcopy__(self, memo):
        return type(self)(deepcopy(self.__underlying, memo))

FrozenDict = ImmutableDict

__all__ = ['ImmutableEnforcerMeta', 'ImmutableDict', 'FrozenDict']
