from itertools import imap, ifilter, izip, count, chain, takewhile
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
    __slots__ = [ 'modulus', '_spokes_iter', '_spokes_cache', '_spokes_set', '_lock' ]
    def __init__(self, modulus, spokes_iter):
        self.modulus = modulus
        self._spokes_iter = spokes_iter
        self._spokes_cache = []
        self._spokes_set = set()
        self._lock = Lock()


    def __iter__(self):
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


    def __contains__(self, elem):
        elem %= self.modulus
        it = iter(self)
        while not self._spokes_cache or elem > self._spokes_cache[-1]:
            next(it)
        return elem in self._spokes_set


    def prune_roots(self, roots):
        to_delete = set()
        for root in roots.iterkeys():
            if root not in self:
                to_delete.add(root)
        for root in to_delete:
            del roots[root]


    def roll(self, cycles, roots):
        self.prune_roots(roots)

        modulus = self.modulus
        if cycles is not None:
            cycler = xrange(modulus,
                            modulus*(cycles+1),
                            modulus)
        else:
            cycler = count(modulus,
                           modulus)

        pop = roots.pop
        for cycle in cycler:
            for spoke in self:
                candidate = cycle + spoke
                root = pop(candidate, False)
                if root:
                    next_candidate = candidate + 2*root
                    while next_candidate in roots \
                          or next_candidate not in self:
                        next_candidate += 2*root
                    roots[next_candidate] = root
                else:
                    roots[candidate**2] = candidate
                    yield candidate

    class __metaclass__(type):
        def __iter__(cls):
            def close_over(prime, last):
                modulus = last.modulus
                return cls(prime * modulus,
                           ( k
                             for i in xrange(prime)
                             for j in last
                             for k in (i * modulus + j,)
                             if k % prime ))

            last = cls(1, iter((1,)))
            for prime in simple():
                yield last
                last = close_over(prime, last)


    def __str__(self):
        return "<%s.%s %d %d>" % (__name__,
                                  type(self).__name__,
                                  self.modulus,
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
        for p in takewhile(lambda x: x < wheel.modulus, simple()):
            roots[p**2] = p
            yield p

    return chain(init(roots), wheel.roll(None, roots))



def variable_wheel():
    roots = {}
    for wheel, prime in izip(Wheel, simple()):
        for yld in wheel.roll(prime-1, roots):
            yield yld




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
