# WARNING. IF USED IMPROPERLY, THE CLASSES IN THIS MODULE RESULT IN
# SOME PRETTY BIZARRE BEHAVIOR. YOU SHOULD ONLY USE INSTANCES OF
# WeakCompoundKey AS KEYS IN A weakref.WeakKeyDictionary

from weakref import ref
from itertools import imap, chain

strong_refs = set()

class WeakCompoundKey(object):
    # The only non-weak references to a WeakCompoundKey object should
    # come from the ref objects it instantiates during __init__ and
    # from the strong_ref set defined in this module. This means that
    # when one of the objects that we reference gets GC'd, we drop all
    # non-weak references to ourself. It's confusing.
    #
    # If you make other non-weak references to WeakCompoundKey
    # instances, strange things will happen

    # can't use __slots__, can't use ImmutableEnforcerMeta
    def __init__(self, *args, **kwargs):
        super(WeakCompoundKey, self).__init__()
        self.__hash = hash(args) ^ hash(frozenset(kwargs.iteritems()))
        strong_refs.add(self)
        self.__refs = frozenset(imap(lambda x: ref(x, lambda _: self.__explode()),
                                     chain(args, kwargs.itervalues())))
    def __explode(self):
        strong_refs.remove(self)
        del self.__refs
        # and the gc claims us
    def __hash__(self):
        return self.__hash

__all__ = ["WeakCompoundKey"]
