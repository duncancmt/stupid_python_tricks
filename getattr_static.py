# ============ getattr_static backported from 3.2 ===========

import types

_sentinel = object()

def getmro_static(klass):
    retval = type.__dict__['__mro__'].__get__(klass)
    if retval is None:
        retval = tuple()
    return retval

def _check_instance(obj, attr):
    instance_dict = {}
    try:
        instance_dict = object.__getattribute__(obj, "__dict__")
    except AttributeError:
        pass
    return dict.get(instance_dict, attr, _sentinel)


def _check_class(klass, attr):
    for entry in getmro_static(klass):
        if _shadowed_dict(type(entry)) is _sentinel:
            try:
                return entry.__dict__[attr]
            except KeyError:
                pass
    return _sentinel

def _is_type(obj):
    try:
        getmro_static(obj)
    except TypeError:
        return False
    return True

def _shadowed_dict(klass):
    dict_attr = type.__dict__["__dict__"]
    if hasattr(dict_attr, "__objclass__"):
        objclass_check = lambda d, entry: d.__objclass__ is entry
    else:
        # PyPy __dict__ descriptors are 'generic' and lack __objclass__
        objclass_check = lambda d, entry: not hasattr(d, "__objclass__")

    for entry in getmro_static(klass):
        try:
            class_dict = dict_attr.__get__(entry)["__dict__"]
        except KeyError:
            pass
        else:
            if not (type(class_dict) is types.GetSetDescriptorType and
                    class_dict.__name__ == "__dict__" and
                    objclass_check(class_dict, entry)):
                return class_dict
    return _sentinel

def getattr_static(obj, attr, default=_sentinel):
    """Retrieve attributes without triggering dynamic lookup via the descriptor
    protocol, __getattr__ or __getattribute__.

    Note: this function may not be able to retrieve all attributes that getattr
    can fetch (like dynamically created attributes) and may find attributes that
    getattr can't (like descriptors that raise AttributeError). It can also
    return descriptor objects instead of instance members in some cases. See the
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
        for entry in getmro_static(type(klass)):
            if _shadowed_dict(type(entry)) is _sentinel:
                try:
                    return entry.__dict__[attr]
                except KeyError:
                    pass
    if default is not _sentinel:
        return default
    raise AttributeError('%s object has no attribute %s' % (repr(type(obj).__name__), repr(attr)))


def hasattr_static(obj, name):
    try:
        getattr_static(obj, name)
    except AttributeError:
        return False
    else:
        return True


def dir_static(obj):
    result = set()
    if _is_type(obj):
        klass = obj
    else:
        klass = type(obj)
        dict_attr = _shadowed_dict(klass)
        if (dict_attr is _sentinel or
            type(dict_attr) is types.MemberDescriptorType):
            try:
                result.update(dict.iterkeys(object.__getattribute__(obj, "__dict__")))
            except AttributeError:
                pass

    dictproxy = type(type.__dict__)
    for entry in getmro_static(klass):
        if _shadowed_dict(type(entry)) is _sentinel:
            try:
                keys = dictproxy.iterkeys(entry.__dict__)
            except TypeError:
                keys = dict.iterkeys(entry.__dict__)
            result.update(keys)

    if obj is klass:
        for entry in getmro_static(type(klass)):
            try:
                keys = dictproxy.iterkeys(entry.__dict__)
            except TypeError:
                keys = dict.iterkeys(entry.__dict__)
            result.update(keys)

    return tuple(result)

__all__ = ["getattr_static", "hasattr_static", "dir_static", "getmro_static"]
