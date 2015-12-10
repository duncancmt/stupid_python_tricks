from itertools import imap, ifilter, cycle, count
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

def fixed_wheel(index):
    """A very fast wheel+sieve prime generator.

    Adapted from http://stackoverflow.com/q/2211990 with an adjustable
    wheel size.
    """

    # precomputation of the wheel
    small_primes = tuple(take(index, simple()))
    primorial = reduce(mul, small_primes)
    wheel = [ i
              for i in xrange(1, primorial+1)
              if all(imap(lambda p: i % p, small_primes)) ]
    skips = [ (wheel[(i + 1) % len(wheel)] - wheel[i]) % primorial
              for i in xrange(len(wheel)) ]
    wheel = frozenset(wheel)

    # populate roots and yield the small primes
    roots = {}
    for p in small_primes:
        s = p**2
        if s > small_primes[-1]:
            roots[s] = p
        yield p

    # roll the wheel
    p = 1
    for incr in cycle(skips):
        p += incr
        if p in roots:
            r = roots[p]
            del roots[p]
            x = p + 2*r
            while x in roots or (x % primorial) not in wheel:
                x += 2*r
            roots[x] = r
        else:
            roots[p**2] = p
            yield p


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
