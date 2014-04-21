# WARNING. IF USED IMPROPERLY, THE CLASS IN THIS MODULE RESULTS IN
# SOME PRETTY BIZARRE BEHAVIOR. YOU SHOULD ONLY USE INSTANCES OF
# WeakCompoundKey AS KEYS IN A weakref.WeakKeyDictionary

from weakref import ref
from itertools import *

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
        self.__hash = hash(args) ^ hash(frozenset(kwargs.iteritems()))
        strong_refs.add(self)
        self.__refs = frozenset(imap(lambda (x,y): (x, self.make_refs(y)),
                                     chain(enumerate(args), kwargs.iteritems())))
    def make_refs(self, *things):
        # we try really, really hard not to accidentally make
        # reference cycles with closures
        def make_callback(others):
            def callback(_):
                if all(imap(lambda x: x() is None, others)):
                    self.__explode()
            return callback

        return tuple(imap(lambda thing: ref(thing,
                                            make_callback(
                                              tuple(
                                                ifilter(lambda x: x is not thing,
                                                        things)))),
                          things))

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
        return self.__hash
    def __eq__(self, other):
        if self is other:
            return True
        def unpack(refs):
            return dict(imap(lambda (x, y):
                               (x, frozenset(imap(lambda ref: ref(), y))),
                             refs))
        self_unpacked = unpack(self.__refs)
        other_unpacked = unpack(other.__refs)
        sentinel = [object()]
        for name in frozenset(chain(self_unpacked.iterkeys(), other_unpacked.iterkeys())):
            if all(imap(lambda (x, y): x == y, product(self_unpacked.get(name, sentinel),
                                                       other_unpacked.get(name, sentinel)))):
                self_unpacked[name] =\
                  other_unpacked[name] =\
                    frozenset(
                      imap(itemgetter(1),
                           frozenset(
                             imap(lambda x: (id(x), x), # force frozenset to compare on identity
                                  chain(self_unpacked[name], other_unpacked[name])))))
            else:
                return False
        def pack(owner, refs):
            return frozenset(imap(lambda (x, y):
                                    (x, owner.make_refs(*y)),
                                  refs.iteritems()))
        self.__refs = pack(self, self_unpacked)
        other.__refs = pack(other, other_unpacked)
        # old refs get GC'd and can no longer cause us to explode
        return True


__all__ = ["WeakCompoundKey"]
