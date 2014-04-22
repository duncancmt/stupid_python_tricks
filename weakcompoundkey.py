# WARNING. IF USED IMPROPERLY, THE CLASS IN THIS MODULE RESULTS IN
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

    # can't use __slots__ (makes things un-weakreference-able)
    # can't use ImmutableEnforcerMeta (we need to delete self.__refs)
    def __init__(self, *args, **kwargs):
        super(WeakCompoundKey, self).__init__()
        self.__refs = frozenset(imap(lambda (x,y): (x, ref(y, lambda _: self.__explode())),
                                     chain(enumerate(args), kwargs.iteritems())))
        strong_refs.add(self)
    def __explode(self):
        # It's possible to call __explode multiple times because
        # callback inside make_refs is not threadsafe. However, this
        # doesn't matter because all we care about is that __explode
        # is called at least once when the strong references are
        # dropped
        try:
            strong_refs.remove(self)
            del self.__refs
        except:
            pass
        # and the GC claims us (sometimes takes more than 1 GC pass,
        # but at this point there are no longer any strong references
        # to ourself)

    def __hash__(self):
        return hash(self.__refs)
    def __eq__(self, other):
        return self.__refs == other.__refs

__all__ = ["WeakCompoundKey"]
