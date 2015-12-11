from itertools import ifilter, count, chain
from operator import mul
from threading import Lock

def simple():
    """A simple prime generator using the Sieve of Eratosthenes.

    This is not intended to be fast, but is instead intended to be so
    simple that its correctness is obvious.
    """
    stream = count(2)
    while True:
        prime = next(stream)
        sieve = (lambda n: lambda i: i % n)(prime)
        stream = ifilter(sieve, stream)
        yield prime

def take(n, stream):
    stream = iter(stream)
    for _ in xrange(n):
        yield next(stream)

def drop(n, stream):
    stream = iter(stream)
    for _ in xrange(n):
        next(stream)
    return stream

def nth(n, stream):
    try:
        return next(take(1, drop(n, stream)))
    except StopIteration:
        raise IndexError("Can't get element off the end of generator")


class Wheel(object):
    __slots__ = [ '_primorial', '_spokes_iter', '_spokes_cache', '_spokes_set', '_lock' ]
    def __init__(self, primorial, spokes_iter):
        self._primorial = primorial
        self._spokes_cache = [next(spokes_iter)]
        self._spokes_iter = spokes_iter
        self._spokes_set = set(self._spokes_cache)
        self._lock = Lock()

    def __len__(self):
        return self._primorial

    def __contains__(self, elem):
        elem %= len(self)
        if elem > self._spokes_cache[-1]:
            it = iter(self.spokes)
            while elem > self._spokes_cache[-1]:
                next(it)
        return elem in self._spokes_set

    @property
    def spokes(self):
        i = 0
        while True:
            while i < len(self._spokes_cache):
                yield self._spokes_cache[i]
                i += 1
            with self._lock:
                if i != len(self._spokes_cache):
                    continue
                try:
                    yld = next(self._spokes_iter)
                except StopIteration:
                    break
                self._spokes_cache.append(yld)
                self._spokes_set.add(yld)
            i += 1
            yield yld

    def __iter__(self):
        return ( n + s
                 for s in count(0, len(self))
                 for n in self.spokes )

    @property
    def bigger(self):
        # TODO: drop references to parent in hopes that it will get
        # collected
        prime = nth(1, self)
        return type(self)(prime * len(self),
                          ifilter(lambda x: x % prime,
                                  ( i + j * len(self)
                                    for j in xrange(prime)
                                    for i in self.spokes ) ))

    class __metaclass__(type):
        def __iter__(cls):
            last = cls(1, iter((1,)))
            while True:
                yield last
                last = last.bigger

    def __str__(self):
        return "<%s.%s %d %d>" % (__name__,
                                  type(self).__name__,
                                  len(self),
                                  id(self))


    def roll(self, roots):
        root = None
        old_roots = set()
        for root in roots.iterkeys():
            # TODO: try to avoid member access here. maybe this whole
            # section is unnecessary?
            if root not in self:
                old_roots.add(root)
        for root in sorted(old_roots):
            del roots[root]
        del old_roots
        del root

        for p in self:
            if p in roots:
                r = roots[p]
                del roots[p]
                x = p + 2*r
                while x in roots or x not in self:
                    x += 2*r
                roots[x] = r
            else:
                roots[p**2] = p
                yield p

def fixed_wheel(index):
    """A very fast wheel+sieve prime generator.

    Adapted from http://stackoverflow.com/q/2211990 with an adjustable
    wheel size.
    """

    # precomputation of the wheel
    wheel = nth(index, Wheel)

    # populate roots and yield the small primes
    roots = {}
    def init():
        for p in take(index, simple()):
            roots[p**2] = p
            yield p
    return chain(init(), drop(1, wheel.roll(roots)))


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print >>sys.stderr, "Usage: %s iterations wheel_index" % sys.argv[0]
        sys.exit(-1)
    iterations = int(sys.argv[1])
    wheel_index = int(sys.argv[2])
    from itertools import imap
    from operator import eq
    print all(imap(eq, take(iterations, simple()),
                       take(iterations, fixed_wheel(wheel_index))))
