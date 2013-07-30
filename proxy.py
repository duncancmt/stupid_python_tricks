# ============ getattr_static backported from 3.2 ===========
import types

_sentinel = object()

def _static_getmro(klass):
    retval = type.__dict__['__mro__'].__get__(klass)
    # if retval is None:
    #     retval = list()
    return retval

def _check_instance(obj, attr):
    instance_dict = {}
    try:
        instance_dict = object.__getattribute__(obj, "__dict__")
    except AttributeError:
        pass
    return dict.get(instance_dict, attr, _sentinel)


def _check_class(klass, attr):
    for entry in _static_getmro(klass):
        if _shadowed_dict(type(entry)) is _sentinel:
            try:
                return entry.__dict__[attr]
            except KeyError:
                pass
    return _sentinel

def _is_type(obj):
    try:
        _static_getmro(obj)
    except TypeError:
        return False
    return True

def _shadowed_dict(klass):
    dict_attr = type.__dict__["__dict__"]
    for entry in _static_getmro(klass):
        try:
            class_dict = dict_attr.__get__(entry)["__dict__"]
        except KeyError:
            pass
        else:
            if not (type(class_dict) is types.GetSetDescriptorType and
                    class_dict.__name__ == "__dict__" and
                    class_dict.__objclass__ is entry):
                return class_dict
    return _sentinel

def getattr_static(obj, attr, default=_sentinel):
    """Retrieve attributes without triggering dynamic lookup via the
       descriptor protocol,  __getattr__ or __getattribute__.

       Note: this function may not be able to retrieve all attributes
       that getattr can fetch (like dynamically created attributes)
       and may find attributes that getattr can't (like descriptors
       that raise AttributeError). It can also return descriptor objects
       instead of instance members in some cases. See the
       documentation for details.
    """
    instance_result = _sentinel
    if not _is_type(obj):
        klass = type(obj)
        dict_attr = _shadowed_dict(klass)
        if (dict_attr is _sentinel or
            type(dict_attr) is types.MemberDescriptorType):
            instance_result = _check_instance(obj, attr)
    else:
        klass = obj

    klass_result = _check_class(klass, attr)

    if instance_result is not _sentinel and klass_result is not _sentinel:
        if (_check_class(type(klass_result), '__get__') is not _sentinel and
            _check_class(type(klass_result), '__set__') is not _sentinel):
            return klass_result

    if instance_result is not _sentinel:
        return instance_result
    if klass_result is not _sentinel:
        return klass_result

    if obj is klass:
        # for types we check the metaclass too
        for entry in _static_getmro(type(klass)):
            if _shadowed_dict(type(entry)) is _sentinel:
                try:
                    return entry.__dict__[attr]
                except KeyError:
                    pass
    if default is not _sentinel:
        return default
    raise AttributeError(attr)

# ============ end getattr_static backported from 3.2 ===========
import inspect

def hasattr_static(obj, name):
    try:
        getattr_static(obj, name)
        return True
    except AttributeError:
        return False

def isdescriptor(obj):
    return ( hasattr_static(obj, '__get__') or \
             hasattr_static(obj, '__set__') or \
             hasattr_static(obj, '__delete__') )

def checkdescriptor(obj, name):
    """returns the descriptor if name is a descriptor in obj, otherwise raises AttributeError"""
    desc = getattr_static(obj, name)
    if isdescriptor(desc):
        return desc
    else:
        raise AttributeError

from abc import ABCMeta

# TODO: this doesn't work: `cls.meth(proxy, *args, **kwargs)` when proxy is a proxy for an object of type cls
class BasicProxy(object):
    """
    A basic proxy class that cannot handle descriptor attributes.
    You should probably subclass Proxy or BetterProxy.

    This class is initialized by giving it an object to proxy.
    Instances of this class behave like the given object in almost all situations.

    Subclasses should override _munge_names (see docstring for BasicProxy._munge)
    """
    # TODO: add bits of the docstrings from _munge and _do_munge and reference them from Proxy's docstring
    
    __metaclass__ = ABCMeta
    
    def __init__(self, obj, *args, **kwargs):
        object.__setattr__(self, "_obj", obj)

    # This is to satisfy the ABCMeta metaclass
    @classmethod
    def __subclasshook__(cls, C):
        return NotImplemented
    
    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        # this prevents infinite recursion
        if name == '_protected_names' or name in self._protected_names:
            return object.__getattribute__(self, name)

        try:
            retval = object.__getattribute__(self, name)
        except AttributeError:
            retval = getattr(self._obj, name)

        return self._munge(name, retval)

    def __delattr__(self, name):
        try:
            object.__delattr__(self, name)
        except AttributeError:
            delattr(self._obj, name)

    def __setattr__(self, name, value):
        try:
            object.__getattribute__(self, name)
            # preceeding line insures that 'name' is directly part of self,
            # not just part of the proxied object
            object.__setattr__(self, name, value)
        except AttributeError:
            setattr(self._obj, name, value)

    # TODO: for some ineffable reason, these have to be explicitly part of the
    # class instead of being handled below
    def __nonzero__(self):
        return bool(self._obj)
    def __str__(self):
        return str(self._obj)
    def __unicode__(self):
        return unicode(self._obj)
    def __repr__(self):
        return repr(self._obj)
    
    #
    # factories
    #
    # __dict__ is deliberately left off this list
    # ABCMeta takes care of __instancecheck__ and __subclasscheck__
    # __get__, __set__, and __delete__ require additional information
    #    and can only be handled by DescriptorProxy below
    # _special_names are *all* methods
    _special_names = frozenset(
        [ '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
          '__complex__', '__contains__', '__delitem__',
          '__delslice__', '__dir__', '__div__', '__divmod__', '__enter__',
          '__eq__', '__exit__', '__float__', '__floordiv__', '__format__',
          '__ge__', '__getitem__', '__getslice__', '__gt__',
          '__hash__', '__hex__', '__iadd__', '__iand__', '__idiv__',
          '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__', '__imul__',
          '__index__', '__int__', '__invert__', '__ior__',
          '__ipow__', '__irshift__', '__isub__', '__iter__', '__itruediv__',
          '__ixor__', '__le__', '__len__', '__long__', '__lshift__', '__lt__',
          '__mod__', '__mul__', '__ne__', '__neg__', '__oct__', '__or__',
          '__pos__', '__pow__', '__radd__', '__rand__', '__rdiv__',
          '__rdivmod__', '__reduce__', '__reduce_ex__', '__reversed__',
          '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__ror__',
          '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__',
          '__rxor__', '__setitem__', '__setslice__', '__sub__',
          '__truediv__', '__xor__', 'next', ])
    _protected_names = frozenset([ '_obj', '_munge', '_do_munge', '_munge_cache', ])
    _munge_names = {}

    def _do_munge(self, munger, name, retval):
        """
        munger may be:
            a method/function which is called with the name and value of the method to be munged
            a name of a method (string) which is looked up using object.__getattribute__ and called as above
            or a list [of lists]* which is traversed, depth first, from first to last, as above
        """
        if callable(munger):
            retval = munger(name, retval)
        if isinstance(munger, basestring):
            retval = object.__getattribute__(self, munger)(name, retval)
        else:
            for m in munger:
                retval = self._do_munge(m, name, retval)
        return retval

    def _munge(self, name, value):
        """
        Arguments:
            name - the name of the attribute to be munged
            value - the attribute to be munged
        Returns: the munged attribute
        
        Search through all the ancestor classes' _munge_names in
        *reverse order* (parent first). For each match of name, modify value
        by replacing it with the return value of the specified munging
        function. If name appears in multiple _munge_names it is munged
        repeatedly, by the parent first, then the child.

        The _munge_names attribute of any subclass should be a mapping from
        method names to descriptioins of how to munge that name (see the
        docstring for _do_munge)
        """

        # This is safe, even with descriptors, because the descriptor will
        # always execute, then only if the result of the descriptor is
        # identical to the cached value, will the cached result be returned
        try:
            cache = self._munge_cache
        except AttributeError:
            cache = {}
            object.__setattr__(self, '_munge_cache', cache)

        if name in cache and value is cache[name][0]:
            return cache[name][1]

        retval = value
        for cls in reversed(type(self).__mro__):
            try:
                # munger can be the name of a method, or a method itself
                munger = cls._munge_names[name]
                retval = self._do_munge(munger, name, value)
            except (KeyError, AttributeError):
                pass
            
        cache[name] = (value, retval)
        return retval

    @classmethod
    def _initialize_namespace(cls, theclass, *args, **kwargs):
        """Create namespace dictionary prior to calling namespace-filling methods"""
        return dict()

    @classmethod
    def _load_special_names(cls, theclass, namespace, *args, **kwargs):
        """Load all relevant special methods into namespace in preparation for creating the proxy class"""
        def make_method(name):
            def method(self, *args, **kw):
                # _special_names are *all* methods, they *must not* be munged to descriptors
                meth = getattr(self._obj, name)
                return self._munge(name, meth)(*args, **kw)
            return method
        
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)

    @classmethod
    def _load_descriptors(cls, theclass, namespace, *args, **kwargs):
        """
        Load all descriptors into namespace in preparation for creating the proxy class.
        This is unimplemented in BasicProxy. If you want this functionality, extend Proxy
        """
        pass

    @classmethod
    def _finalize_namespace(cls, theclass, namespace, *args, **kwargs):
        """Make final tweaks to namespace prior to creating the proxy class"""
        # needed to proxy class descriptor attributes
        namespace['_class'] = theclass

    @classmethod
    def _create_class_proxy(cls, theclass, *args, **kwargs):
        """
        Creates a proxy for the given class
        Calls the following hooks in order:
            _initialize_namespace
            _load_special_names
            _load_descriptors
            _finalize_namespace
        """

        namespace = cls._initialize_namespace(theclass, *args, **kwargs)
        cls._load_special_names(theclass, namespace, *args, **kwargs)
        cls._load_descriptors(theclass, namespace, *args, **kwargs)
        cls._finalize_namespace(theclass, namespace, *args, **kwargs)

        try:
            retval = cls.__metaclass__("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
        except AttributeError:
            retval = type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
        retval.register(retval._class)
        return retval

    @classmethod
    def _get_class_proxy(cls, obj, *args, **kwargs):
        """
        Return the proxy class from the cache if it's already been created.
        Otherwise, create it and return it.
        """
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}

        try:
            theclass = cache[obj.__class__]
        except KeyError:
            theclass = cls._create_class_proxy(obj.__class__, *args, **kwargs)
            try:
                cache[(obj.__class__, tuple(args), tuple(sorted(kwargs.iteritems())))] = theclass
            except TypeError:
                pass
        return theclass
    
    def __new__(cls, obj, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        theclass = cls._get_class_proxy(obj, *args, **kwargs)
        ins = object.__new__(theclass)
        theclass.__init__(ins, obj, *args, **kwargs)
        return ins

class DescriptorProxy(BasicProxy):
    """
    This class and subclasses implement a proxy for descriptor attributes.
    You can modify the behavior of __get__, __set__, and __delete__ from here.

    Subclasses should override the classmethod _generate_descriptor_methods.
    This classmethod takes 4 arguments: the attribute name and whether
    (__get__, __set__, __delete__) are present in the underlying descriptor.
    _generate_descriptor_methods should return a 3-tuple of (get, set, delete)
    functions to be bound as methods in the descriptor proxy. If non-callable
    objects are supplied as any of (get, set, delete), then that method will
    be missing in the descriptor proxy. If _generate_descriptor_methods raises
    AttributeError, the descriptor will not be proxied by this descriptor
    proxy. (it may still be proxied by subclasses)

    Inside the methods supplied by _generate_descriptor_methods, the underlying
    descriptor is available as self._obj . The instance that the descriptor
    proxy belongs to is instance._obj. The class that the descriptor belongs to
    is owner._class.
    """    
    @classmethod
    def _generate_descriptor_methods(cls, name, has_get=False,
                                                has_set=False,
                                                has_delete=False):
        # self._obj will always return the underlying descriptor, not cause code execution
        # because self._obj is inserted into the instance dict, not the class dict.

        if has_get:
            def get(self, instance, owner):
                if instance is None:
                    return self._obj.__get__(None, owner._class)
                else:
                    return self._obj.__get__(instance._obj, owner._class)
        else:
            get = None

        if has_set:
            def set(self, instance, value):
                return self._obj.__set__(instance._obj, value)
        else:
            set = None

        if has_delete:
            def delete(self, instance):
                return self._obj.__delete__(instance._obj)
        else:
            delete = None
            
        return (get, set, delete)
    
    @classmethod
    def _finalize_namespace(cls, theclass, namespace, name):
        (get, set, delete) = cls._generate_descriptor_methods(name,
                                                              hasattr_static(theclass, '__get__'),
                                                              hasattr_static(theclass, '__set__'),
                                                              hasattr_static(theclass, '__delete__'))
        if callable(get):
            namespace['__get__'] = get

        if callable(set):
            namespace['__set__'] = set
            
        if callable(delete):
            namespace['__delete__'] = delete

        super(DescriptorProxy, cls)._finalize_namespace(theclass, namespace)

class Proxy(BasicProxy):
    """
    A proxy class that _can_ handle descriptor attributes.

    This class is initialized by giving it an object to proxy.
    Instances of this class behave like the given object in almost all situations.

    Subclasses should override _descriptor_proxy_class (see docstring for DescriptorProxy)
    and _munge_names (see docstring for BasicProxy._munge)

    Descriptor proxies are applied in reverse order. The parent's descriptor proxy is applied first.

    Special methods that are descriptors are excluded from modification.
    It should be noted that methods, classmethods, and staticmethods are all descriptors.
    """
    
    _descriptor_proxy_class = DescriptorProxy
    _no_descriptor_proxy_names = frozenset(['__get__', '__set__', '__delete__']) | frozenset(BasicProxy.__dict__.keys())

    @classmethod
    def _load_descriptors(cls, theclass, namespace, *args, **kwargs):
        """Load all descriptors into namespace in preparation for creating the proxy class."""
        for name in dir(theclass):
            if name in cls._no_descriptor_proxy_names \
                   or name in namespace:
                # Names in the namespace and _no_descriptor_proxy_names are those that
                # sometimes get looked up by Python's internals. Making descriptor
                # proxies of those names results in very strange behavior.
                continue
            attr = getattr_static(theclass, name)

            if isdescriptor(attr):
                for klass in reversed(cls.__mro__):
                    try:
                        namespace[name] = attr = klass._descriptor_proxy_class(attr, name)
                    except AttributeError:
                        continue
        
        super(Proxy, cls)._load_descriptors(theclass, namespace)


class BetterProxy(Proxy):
    """
    This proxy class attempts to proxy the return values of the __i*__ methods.
    These methods would normally return an un-proxied objecy.

    If aggressive=True is passed, we will also attempt to proxy the output of
    the normal arithmetic __*__ methods.

    For further information, see docstring for Proxy
    """

    @classmethod
    def _finalize_namespace(cls, theclass, namespace, aggressive=False, *args, **kwargs):
        """
        If a __i*__ method is not defined, but the corresponding __*__ is,
        define a __i*__ method with appropriate semantics.
        Handle aggressive proxying.
        """
        def make_imethod(name):
            def method(self, *args, **kwargs):
                return cls(getattr(self, name)(*args, **kwargs), aggressive=aggressive)
            return method

        def make_method(old):
            def method(self, *args, **kwargs):
                return cls(old(self, *args, **kwargs), aggressive=aggressive)
            return method

        for name, iname in [('__add__', '__iadd__'),
                            ('__sub__', '__isub__'),
                            ('__mul__', '__imul__'),
                            ('__div__', '__idiv__'),
                            ('__truediv__', '__itruediv__'),
                            ('__floordiv__', '__ifloordiv__'),
                            ('__mod__', '__imod__'),
                            ('__pow__', '__ipow__'),
                            ('__lshift__', '__ilshift__'),
                            ('__rshift__', '__irshift__'),
                            ('__and__', '__iand__'),
                            ('__xor__', '__ixor__'),
                            ('__or__', '__ior__')]:
            if name in namespace:
                if aggressive:
                    namespace[name] = make_method(namespace[name])
                elif iname not in namespace:
                    namespace[iname] = make_imethod(name)

        namespace['_aggressive'] = aggressive
        super(BetterProxy, cls)._finalize_namespace(theclass, namespace, aggressive=aggressive,
                                                    *args, **kwargs)

    def _reproxy(self, name, value):
        cls = type(self)

        if callable(value):
            def munged(*args, **kwargs):
                retval = value(*args, **kwargs)
                if isinstance(retval, cls):
                    return retval
                else:
                    return cls(retval, aggressive=cls._aggressive)
            return munged
        else:
            return cls(value)
        
    _munge_names = { '__iadd__':'_reproxy',
                     '__isub__':'_reproxy',
                     '__imul__':'_reproxy',
                     '__idiv__':'_reproxy',
                     '__itruediv__':'_reproxy',
                     '__ifloordiv__':'_reproxy',
                     '__imod__':'_reproxy',
                     '__ipow__':'_reproxy',
                     '__ilshift__':'_reproxy',
                     '__irshift__':'_reproxy',
                     '__iand__':'_reproxy',
                     '__ixor__':'_reproxy',
                     '__ior__':'_reproxy', }

__all__ = ["BasicProxy", "Proxy", "BetterProxy", "DescriptorProxy"]
