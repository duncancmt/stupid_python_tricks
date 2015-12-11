from itertools import ifilter, izip, cycle, count, chain
from operator import mul

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
    __slots__ = [ 'primorial', 'spokes', 'spokes_set' ]
    def __init__(self, primorial, spokes):
        self.primorial = primorial
        self.spokes = spokes
        self.spokes_set = frozenset(spokes)
    def __iter__(self):
        return ( n + s
                 for s in count(0, self.primorial)
                 for n in self.spokes )
    class __metaclass__(type):
        def __iter__(cls):
            # TODO: because we don't cache the most immediate result,
            # this produces lots of unnecessary recursion
            yield cls(1, (1,))
            for prime, wheel in izip(primes(), cls):
                yield cls(prime*wheel.primorial,
                          tuple(ifilter(lambda x: x % prime,
                                        ( i+j*wheel.primorial
                                          for j in xrange(prime)
                                          for i in wheel.spokes ) )))

def roll(wheel, roots):
    root = None
    old_roots = set()
    for root in roots.iterkeys():
        # TODO: try to avoid member access here. maybe this whole
        # section is unnecessary?
        if root % primorial not in wheel.spokes_set:
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
            while x in roots or (x % wheel.primorial) not in wheel.spokes_set:
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
        for p in take(index, primes()):
            roots[p**2] = p
            yield p
    return chain(init(), drop(1, roll(wheel, roots)))

primes = simple

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
