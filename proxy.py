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


from abc import ABCMeta

from getattr_static import *

# TODO: this doesn't work: `cls.meth(proxy, *args, **kwargs)` when proxy is a proxy for an object of type cls
class BasicProxy(object):
    """
    A basic proxy class that cannot handle descriptor attributes.
    You should probably subclass Proxy or BetterProxy.

    This class is initialized by giving it an object to proxy.
    Instances of this class behave like the given object in almost all
    situations.

    Subclasses should override _munge_names (see docstring for
    BasicProxy._munge)

    Adapted from ActiveState recipe 496741
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
        except AttributeError:
            setattr(self._obj, name, value)
        else:
            object.__setattr__(self, name, value)

    # python automatically defines these methods for all new-style classes, to
    # avoid shadowing the original object, we must explicitly define these
    # ourselves.
    @property
    def __doc__(self):
        return self._obj.__doc__
    def __format__(self, format_spec):
        return format(self._obj, format_spec)
    def __hash__(self):
        return hash(self._obj)
    def __nonzero__(self):
        return bool(self._obj)
    def __repr__(self):
        return repr(self._obj)
    def __str__(self):
        return str(self._obj)
    def __unicode__(self):
        return unicode(self._obj)

    #
    # factories
    #
    # __dict__ is deliberately left off this list
    # ABCMeta takes care of __instancecheck__ and __subclasscheck__
    # __get__, __set__, and __delete__ require additional information
    #    and can only be handled by DescriptorProxy below
    # _special_names are *all* methods
    _special_names = frozenset([ '__abs__', '__add__', '__and__', '__call__',
        '__cmp__', '__coerce__', '__complex__', '__contains__', '__delitem__',
        '__delslice__', '__dir__', '__div__', '__divmod__', '__enter__',
        '__eq__', '__exit__', '__float__', '__floordiv__', '__ge__',
        '__getitem__', '__getslice__', '__gt__', '__hex__', '__iadd__',
        '__iand__', '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__',
        '__imod__', '__imul__', '__index__', '__int__', '__invert__', '__ior__',
        '__ipow__', '__irshift__', '__isub__', '__iter__', '__itruediv__',
        '__ixor__', '__le__', '__len__', '__long__', '__lshift__', '__lt__',
        '__mod__', '__mul__', '__ne__', '__neg__', '__oct__', '__or__',
        '__pos__', '__pow__', '__radd__', '__rand__', '__rdiv__', '__rdivmod__',
        '__reduce__', '__reduce_ex__', '__reversed__', '__rfloordiv__',
        '__rlshift__', '__rmod__', '__rmul__', '__ror__', '__rpow__',
        '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__', '__rxor__',
        '__setitem__', '__setslice__', '__sub__', '__truediv__', '__xor__',
        'next', ])
    _protected_names = frozenset([ '_obj', '_munge', '_do_munge', '_munge_cache', ])
    _munge_names = {}

    def _do_munge(self, munger, name, retval):
        """
        munger may be:
            a method/function which is called with the name and value of the
                method to be munged
            a name of a method (string) which is looked up using
                object.__getattribute__ and called as above
            or a list [of lists]* which is traversed, depth first, from first to
                last, as above
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
        
        Search through all the ancestor classes' _munge_names in *reverse order*
        (parent first). For each match of name, modify value by replacing it
        with the return value of the specified munging function. If name appears
        in multiple _munge_names it is munged repeatedly, by the parent first,
        then the child.

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
    def _initialize_namespace(cls, objclass, *args, **kwargs):
        """Create namespace dictionary prior to calling namespace-filling
        methods"""
        return dict()

    @classmethod
    def _load_special_names(cls, objclass, namespace, *args, **kwargs):
        """Load all relevant special methods into namespace in preparation for
        creating the proxy class"""
        def make_method(name):
            def method(self, *args, **kw):
                # _special_names are *all* methods, they *must not* be munged to descriptors
                meth = getattr(self._obj, name)
                return self._munge(name, meth)(*args, **kw)
            return method
        
        for name in cls._special_names:
            if hasattr(objclass, name) and not hasattr(cls, name):
                namespace[name] = make_method(name)

    @classmethod
    def _load_descriptors(cls, objclass, namespace, *args, **kwargs):
        """
        Load all descriptors into namespace in preparation for creating the
        proxy class.

        This is unimplemented in BasicProxy. If you want this functionality,
        extend Proxy
        """
        pass

    @classmethod
    def _finalize_namespace(cls, objclass, namespace, *args, **kwargs):
        """Make final tweaks to namespace prior to creating the proxy class"""
        # needed to proxy class descriptor attributes
        namespace['_class'] = objclass

    @classmethod
    def _create_class_proxy(cls, objclass, *args, **kwargs):
        """
        Creates a proxy for the given class
        Calls the following hooks in order:
            _initialize_namespace
            _load_special_names
            _load_descriptors
            _finalize_namespace
        """

        namespace = cls._initialize_namespace(objclass, *args, **kwargs)
        cls._load_special_names(objclass, namespace, *args, **kwargs)
        cls._load_descriptors(objclass, namespace, *args, **kwargs)
        cls._finalize_namespace(objclass, namespace, *args, **kwargs)

        try:
            retval = cls.__metaclass__("%s(%s)" % (cls.__name__, objclass.__name__), (cls,), namespace)
        except AttributeError:
            retval = type("%s(%s)" % (cls.__name__, objclass.__name__), (cls,), namespace)
        retval.register(retval._class)
        return retval

    @classmethod
    def _get_class_proxy(cls, obj, *args, **kwargs):
        """
        Return the proxy class from the cache if it's already been created.
        Otherwise, create it and return it.
        """
        if hasattr(cls, "_class"):
            # For programmatically derived classes, get the original cache
            cls = cls.__mro__[1]
            cache = cls.__dict__["_class_proxy_cache"]
        else:
            try:
                cache = cls.__dict__["_class_proxy_cache"]
            except KeyError:
                cls._class_proxy_cache = cache = {}

        key = (type(obj), tuple(args), tuple(sorted(kwargs.iteritems())))
        try:
            proxy_class = cache[key]
        except KeyError:
            proxy_class = cls._create_class_proxy(type(obj), *args, **kwargs)
            try:
                cache[key] = proxy_class
            except TypeError:
                pass
        return proxy_class
    
    def __new__(cls, obj, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        proxy_class = cls._get_class_proxy(obj, *args, **kwargs)
        ins = object.__new__(proxy_class)
        # It is unnecessary to call __init__ directly here.
        # python will call it after __new__ because isinstance(ins, cls)
        return ins



def isdescriptor(obj):
    return ( hasattr_static(obj, '__get__') or \
             hasattr_static(obj, '__set__') or \
             hasattr_static(obj, '__delete__') )

def checkdescriptor(obj, name):
    """returns the descriptor if name is a descriptor in obj, otherwise raises
    AttributeError"""
    desc = getattr_static(obj, name)
    if isdescriptor(desc):
        return desc
    else:
        raise AttributeError


class DifficultDescriptorProxy(BasicProxy):
    """
    You probably want to use DescriptorProxy. It has a better interface.

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
    proxy. (it may still be proxied by the descriptor proxy class of an
    ancestor of the normal proxy class)

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
    def _finalize_namespace(cls, objclass, namespace, name):
        (get, set, delete) = cls._generate_descriptor_methods(name,
                                                              hasattr_static(objclass, '__get__'),
                                                              hasattr_static(objclass, '__set__'),
                                                              hasattr_static(objclass, '__delete__'))
        if callable(get):
            namespace['__get__'] = get

        if callable(set):
            namespace['__set__'] = set
            
        if callable(delete):
            namespace['__delete__'] = delete

        super(DifficultDescriptorProxy, cls)._finalize_namespace(objclass, namespace)


class DescriptorProxy(DifficultDescriptorProxy):
    """
    This class and subclasses implement a proxy for descriptor attributes.
    You can modify the behavior of __get__, __set__, and __delete__ from here.

    Subclasses should override the methods _proxy__get__, _proxy__set__, and
    _proxy__delete__. Their signatures are:
        _proxy__get__(self, attribute_name, instance, owner)
        _proxy__set__(self, attribute_name, instance, value)
        _proxy__delete__(self, attribute_name, instance)

    Inside these methods, the underlying descriptor is available as self._obj
    The instance that the descriptor proxy belongs to is instance._obj
    The class that the descriptor belongs to is owner._class
    """
    @classmethod
    def _generate_descriptor_methods(cls, name, has_get=False,
                                                has_set=False,
                                                has_delete=False):
        # self._obj will always return the underlying descriptor, not cause code execution
        # because self._obj is inserted into the instance dict, not the class dict.

        if has_get:
            _proxy__get__ = getattr_static(cls, '_proxy__get__')
            def get(self, instance, owner):
                return _proxy__get__(self, name, instance, owner)
        else:
            get = None

        if has_set:
            _proxy__set__ = getattr_static(cls, '_proxy__set__')
            def set(self, instance, value):
                return _proxy__set__(self, name, instance, value)
        else:
            set = None

        if has_delete:
            _proxy__delete__ = getattr_static(cls, '_proxy__delete__')
            def delete(self, instance):
                return _proxy__delete__(self, name, instance)
        else:
            delete = None
            
        return (get, set, delete)

    def _proxy__get__(self, name, instance, owner):
        if instance is None:
            return self._obj.__get__(None, owner._class)
        else:
            return self._obj.__get__(instance._obj, owner._class)

    def _proxy__set__(self, name, instance, value):
        return self._obj.__set__(instance._obj, value)

    def _proxy__delete__(self, name, instance):
        return self._obj.__delete__(instance._obj)


class DifficultProxy(BasicProxy):
    """You probably want to use Proxy instead of this class. If you use this
    class you will have trouble handling objects just after they're allocated,
    but before they're initialized."""
    _descriptor_proxy_class = DescriptorProxy
    _no_descriptor_proxy_names = frozenset(['__getattribute__'])
    @classmethod
    def _load_descriptors(cls, objclass, namespace, *args, **kwargs):
        """Load all descriptors into namespace in preparation for creating the proxy class."""
        for name in dir_static(objclass):
            if name in cls._no_descriptor_proxy_names \
                   or name in namespace \
                   or hasattr_static(cls, name):
                # Names in the namespace and _no_descriptor_proxy_names are
                # those that sometimes get looked up by Python's
                # internals. Making descriptor proxies of those names results in
                # very strange behavior. Names that are already attributes of
                # cls have special-case behavior defined by a child class.
                continue
            attr = getattr_static(objclass, name)

            if isdescriptor(attr):
                # TODO: come up with some sort of sane inheritance mechanism for descriptor proxies
                for klass in cls.__mro__:
                    try:
                        namespace[name] = klass.__dict__['_descriptor_proxy_class'](attr, name)
                    except (AttributeError, KeyError):
                        continue
                    else:
                        break


class Proxy(DifficultProxy):
    """
    A proxy class that _can_ handle descriptor attributes.

    This class is initialized by giving it an object to proxy.
    Instances of this class behave like the given object in almost all
    situations.

    Subclasses should override _descriptor_proxy_class (see docstring for
    DescriptorProxy) and _munge_names (see docstring for BasicProxy._munge)

    The first descriptor proxy class to not raise AttributeError is the one
    that is applied to that descriptor attribute. Descriptor proxy classes
    are traversed in the same order as the proxy class' MRO.

    Special methods that are descriptors are excluded from modification.
    It should be noted that methods, classmethods, and staticmethods are all
    descriptors.
    """
    _no_descriptor_proxy_names = frozenset(BasicProxy.__dict__.keys())


class BetterDescriptorProxy(DescriptorProxy):
    def _proxy__get__(self, name, instance, owner):
        try:
            return self._obj.__get__(instance, owner)
        except TypeError as e:
            if len(e.args) == 1 \
               and e.args[0].startswith('descriptor'):
                return super(BetterDescriptorProxy, self)._proxy__get__(name, instance, owner)
            raise

    def _proxy__set__(self, name, instance, value):
        return self._obj.__set__(instance._obj, value)

    def _proxy__delete__(self, name, instance):
        return self._obj.__delete__(instance._obj)

class BetterProxy(Proxy):
    """
    This proxy class attempts to proxy the return values of the __i*__ methods.
    These methods would normally return an un-proxied object.

    If aggressive=True is passed, we will also attempt to proxy the output of
    the normal arithmetic __*__ methods.

    Method binding is also performed on the proxy object instead of the
    underlying object. That means that the methods of the underlying object
    are "stolen" by the proxy object when looked up and "self" inside these
    stolen methods refers to the proxy object, not the underlying object.

    For further information, see docstring for Proxy
    """
    _descriptor_proxy_class = BetterDescriptorProxy

    @classmethod
    def _finalize_namespace(cls, objclass, namespace, aggressive=False, *args, **kwargs):
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
        super(BetterProxy, cls)._finalize_namespace(objclass, namespace, aggressive=aggressive,
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

__all__ = ["BasicProxy", "Proxy", "DescriptorProxy", "BetterProxy", "BetterDescriptorProxy"]
