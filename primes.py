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

def wheels():
    yield (1, [1])
    for prime, (primorial, wheel) in izip(primes(), wheels()):
        yield (prime*primorial, filter(lambda x: x % prime,
                                       ( i+j*primorial
                                         for j in xrange(prime)
                                         for i in wheel ) ))

def roll_wheel(primorial, wheel, roots):
    root = None
    old_roots = set()
    for root in roots.iterkeys():
        if root % primorial not in wheel:
            old_roots.add(root)
    for root in sorted(old_roots):
        del roots[root]
    del old_roots
    del root

    wheel_set = frozenset(wheel)
    for s in count(0, primorial):
        for n in wheel:
            p = n + s
            if p in roots:
                r = roots[p]
                del roots[p]
                x = p + 2*r
                while x in roots or (x % primorial) not in wheel_set:
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
    primorial, wheel = nth(index, wheels())

    # populate roots and yield the small primes
    roots = {}
    def init():
        for p in take(index, primes()):
            roots[p**2] = p
            yield p
    return chain(init(), drop(1, roll_wheel(primorial, wheel, roots)))

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
