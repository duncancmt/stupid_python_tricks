from collections import MutableMapping
from inspect import isroutine
from proxy import BetterProxy, BetterDescriptorProxy

class TimeoutError(RuntimeError):
    pass

class RepetitiveDict(MutableMapping):
    def __init__(self, value, ignore=[], *args, **kwargs):
        self._value = value
        self._ignore = ignore
        super(RepetitiveDict,self).__init__(*args, **kwargs)
    def __getitem__(self,key):
        if key in self._ignore:
            raise KeyError(key)
        else:
            return self._value
    def __iter__(self):
        return iter([])
    def __len__(self):
        return 0
    def __setitem__(self,key,value):
        pass
    def __delitem__(self,key):
        pass

class TimeoutDescriptorProxy(BetterDescriptorProxy):
    def _proxy__get__(self, attribute_name, instance, owner):
        if instance is not None:
            instance.check_timeout()
        return super(TimeoutDescriptorProxy, self)._proxy__get__(attribute_name, instance, owner)

    def _proxy__set__(self, attribute_name, instance, value):
        instance.check_timeout()
        return super(TimeoutDescriptorProxy, self)._proxy__set__(attribute_name, instance, value)
    
    def _proxy__delete__(self, attribute_name, instance):
        instance.check_timeout()
        return super(TimeoutDescriptorProxy, self)._proxy__delete__(attribute_name, instance)

class TimeoutWrapper(BetterProxy):
    _descriptor_proxy_class = TimeoutDescriptorProxy
    _munge_names = RepetitiveDict("_add_timeout",["_timed_out"])

    def __init__(self,*args,**kwargs):
        object.__setattr__(self, "_timed_out", False)
        super(TimeoutWrapper,self).__init__(*args,**kwargs)

    def _add_timeout(self, name, value):
        if isroutine(value):
            # this may be superfluous because any accesses to "self" inside
            # the method will raise TimeoutError
            def with_timeout(*args, **kwargs):
                if self._timed_out:
                    raise TimeoutError
                else:
                    return value(*args, **kwargs)
            return with_timeout
        
        else:
            if self._timed_out:
                raise TimeoutError
            else:
                return value
        
    def timeout(self):
        self._timed_out = True

    def check_timeout(self):
        pass

__all__ = ["TimeoutWrapper", "TimeoutError"]
