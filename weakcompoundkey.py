# WARNING. IF USED IMPROPERLY, THE CLASS IN THIS MODULE RESULTS IN SOME PRETTY
# BIZARRE BEHAVIOR. YOU SHOULD ONLY USE INSTANCES OF WeakCompoundKey or
# WeakCompoundKeyStrict AS KEYS IN A weakref.WeakKeyDictionary

from weakref import ref
from itertools import imap, chain, ifilter, product
from operator import itemgetter

strong_refs = set()

class WeakCompoundKeyStrict(object):
    """WeakCompoundKeyStrict groups together its hashable arguments and provides a
    single object that can be used as the key to a WeakKeyDictionary that only
    compares equal to another WeakCompoundKeyStrict object that was instantiated with
    the same arguments. A use of this combination is memoization where lines
    from the memoization table should be deleted when the original object that
    produced that line dies.

    Notably, WeakCompoundKey *DOES NOT* inherit from WeakCompoundKeyStrict or
    vice versa.

    The only non-weak references to a WeakCompoundKeyStrict object should come
    from the ref objects it instantiates during __init__ and from the strong_ref
    set defined in this module. This means that when one of the objects that we
    reference gets GC'd, we drop all non-weak references to ourself. It's
    confusing. If you make other non-weak references to WeakCompoundKeyStrict
    instances, strange things will happen
    """

    # can't use __slots__ (makes things un-weakreference-able)
    # can't use ImmutableEnforcerMeta (we need to delete self.__refs)
    def __init__(self, *args, **kwargs):
        super(WeakCompoundKeyStrict, self).__init__()
        self.__refs = frozenset(imap(lambda (x,y): (x, ref(y, lambda _: self.__explode())),
                                     chain(enumerate(args), kwargs.iteritems())))
        strong_refs.add((id(self), self))
    def __explode(self):
        # It's possible to call __explode multiple times because
        # callback inside make_refs is not threadsafe. However, this
        # doesn't matter because all we care about is that __explode
        # is called at least once when the strong references are
        # dropped
        try:
            strong_refs.remove((id(self), self))
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


class WeakCompoundKey(object):
    """WeakCompoundKey does the same thing as WeakCompoundKeyStrict, except
    that when two keys are compared and compare equal, both will only be
    deallocated when all of a group of subelements for a particular argument,
    have been deallocated. Basically, WeakCompoundKey is contaminative
    when keys are compared. WeakCompoundKey is typically used as a key to
    a WeakKeyDictionary where you want the dictionary to compare on `==' instead
    of `is'.

    Notably, WeakCompoundKey *DOES NOT* inherit from WeakCompoundKeyStrict or
    vice versa.

    The only non-weak references to a WeakCompoundKey object should come
    from the ref objects it instantiates during __init__ and from the strong_ref
    set defined in this module. This means that when one of the objects that we
    reference gets GC'd, we drop all non-weak references to ourself. It's
    confusing. If you make other non-weak references to WeakCompoundKey
    instances, strange things will happen


    Example usage:
    from weakref import ref
    from weakcompoundkey import WeakCompoundKey
    class Foo(object):
        def __init__(self, bar):
            self.bar = bar
        def __hash__(self):
            return hash(self.bar) ^ hash(type(self))
        def __eq__(self, other):
            return self.bar == other.bar
        def __del__(self):
            print "I die", str(self.bar)
    a = Foo(1)
    b = Foo(1)
    c = ref(WeakCompoundKey(a))
    d = ref(WeakCompoundKey(b))
    c() is None # False
    d() is None # False
    c() == d() # True
    del a # prints "I die 1"
    c() is None # False, if we were using WeakCompoundKeyStrict, this would be True
    d() is None # False, as expected
    del b # prints "I die 1"
    c() is None # True
    d() is None # True
    """

    # can't use __slots__ (makes things un-weakreference-able)
    # can't use ImmutableEnforcerMeta (we need to delete self.__refs)
    def __init__(self, *args, **kwargs):
        super(WeakCompoundKey, self).__init__()
        self.__hash = hash(args) ^ hash(frozenset(kwargs.iteritems()))
        self.__refs = frozenset(imap(lambda (x,y): (x, self.make_refs(y)),
                                     chain(enumerate(args), kwargs.iteritems())))
        strong_refs.add((id(self), self))

    def make_refs(self, *things):
        # we try really, really hard not to accidentally make
        # reference cycles with closures
        return tuple(imap(lambda thing: ref(thing,
                                            self.make_callback(
                                              tuple(
                                                imap(ref, ifilter(lambda x: x is not thing,
                                                                  things))))),
                          things))

    def make_callback(weakcompound_instance, other_weakrefs):
        # this method has to be separate from make_refs to avoid making
        # reference cycles
        def callback(this_weakref):
            if all(imap(lambda x: x() is None, other_weakrefs)):
                weakcompound_instance.__explode()
        return callback

    def __explode(self):
        # It's possible to call __explode multiple times because
        # callback inside make_refs is not threadsafe. However, this
        # doesn't matter because all we care about is that __explode
        # is called at least once when the strong references are
        # dropped
        try:
            strong_refs.remove((id(self), self))
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
        if self.__hash != other.__hash:
            return False
        def unpack(refs):
            return dict(imap(lambda (x, y):
                               (x, frozenset(ifilter(lambda thing: thing is not None,
                                                     imap(lambda r: r(), y)))),
                             refs))
        self_unpacked = unpack(self.__refs)
        other_unpacked = unpack(other.__refs)
        sentinel = [object()]
        for name in frozenset(chain(self_unpacked.iterkeys(), other_unpacked.iterkeys())):
            if all(imap(lambda (x, y): x == y, product(self_unpacked.get(name, sentinel),
                                                       other_unpacked.get(name, sentinel)))):
                self_unpacked[name] =\
                  other_unpacked[name] =\
                    tuple(
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

__all__ = ["WeakCompoundKeyStrict", "WeakCompoundKey"]
