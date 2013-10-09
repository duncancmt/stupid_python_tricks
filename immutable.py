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
                    raise AttributeError('Cannot mutate private attribute of %s' % repr(self))
                mro = mro_getter(type(self))
                if mro is None:
                    mro = tuple()
                for c in mro:
                    if name in type_dict_getter(c):
                        raise AttributeError('Cannot mutate private attribute of %s' % repr(self))
            return old_setattr(self, name, value)

        def __delattr__(self, name):
            if name[0] == '_':
                if name in object_dict_getter(self):
                    raise AttributeError('Cannot delete private attribute of %s' % repr(self))
                mro = mro_getter(type(self))
                if mro is None:
                    mro = tuple()
                for c in mro:
                    if name in type_dict_getter(c):
                        raise AttributeError('Cannot delete private attribute of %s' % repr(self))
            return old_delattr(self, name)

        namespace = dict(namespace)
        namespace['__setattr__'] = __setattr__
        namespace['__delattr__'] = __delattr__
        namespace['__immutable__'] = False
        cls = super(ImmutableEnforcerMeta, mcls).__new__(mcls, name, bases, namespace)
        cls.__immutable__ = True
        return cls


    def __setattr__(cls, name, value):
        mro_getter = type.__dict__['__mro__'].__get__
        dict_getter = type.__dict__['__dict__'].__get__
        static_setattr = type.__setattr__

        if name[0] == '_' and cls.__immutable__:
            mro = mro_getter(cls)
            if mro is None:
                mro = tuple()
            for c in mro:
                if name in dict_getter(c):
                    raise AttributeError('Cannot mutate private attribute of %s' % repr(cls))
        return static_setattr(cls, name, value)


    def __delattr__(cls, name):
        mro_getter = type.__dict__['__mro__'].__get__
        dict_getter = type.__dict__['__dict__'].__get__
        static_setattr = type.__setattr__

        if name[0] == '_' and cls.__immutable__:
            mro = mro_getter(cls)
            if mro is None:
                mro = tuple()
            for c in mro:
                if name in dict_getter(c):
                    raise AttributeError('Cannot delete private attribute of %s' % repr(cls))
        return static_setattr(cls, name, value)


__all__ = ['ImmutableEnforcerMeta']
