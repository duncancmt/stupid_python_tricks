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
    __slots__ = [ '_modulus', '_spokes_iter', '_spokes_cache', '_lock' ]
    def __init__(self, modulus, spokes_iter):
        self._modulus = modulus
        self._spokes_iter = spokes_iter
        self._spokes_cache = []
        self._lock = Lock()

    def __len__(self):
        return self._modulus

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
            i += 1
            yield yld

    def __iter__(self):
        # TODO: make this slightly more efficient
        return ( n + s
                 for s in count(0, len(self))
                 for n in self.spokes )

    @property
    def bigger(self):
        prime = nth(1, self)
        modulus = len(self)
        return type(self)(prime * modulus,
                          ( k
                            for i in xrange(prime)
                            for j in self.spokes
                            for k in (i * modulus + j,)
                            if k % prime ))

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


def fixed_wheel(index):
    """A very fast wheel+sieve prime generator.

    Adapted from http://stackoverflow.com/q/2211990 with an adjustable
    wheel size.
    """

    # precomputation of the wheel
    wheel = nth(index, Wheel)

    # populate roots and yield the small primes
    roots = {}
    def init(roots):
        for p in take(index, simple()):
            roots[p**2] = p
            yield p

    # roll the wheel and filter the results
    def roll(wheel, roots):
        spokes_set = frozenset(wheel.spokes)
        modulus = len(wheel)

        root = None
        old_roots = set()
        for root in roots.iterkeys():
            if root % modulus not in spokes_set:
                old_roots.add(root)
        for root in sorted(old_roots):
            del roots[root]
        del old_roots
        del root

        for p in wheel:
            if p in roots:
                r = roots[p]
                del roots[p]
                x = p + 2*r
                while x in roots or (x % modulus) not in spokes_set:
                    x += 2*r
                roots[x] = r
            else:
                roots[p**2] = p
                yield p

    return chain(init(roots), drop(1, roll(wheel, roots)))


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
