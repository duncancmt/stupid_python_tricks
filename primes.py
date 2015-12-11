from itertools import imap, ifilter, cycle, count, chain
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
    small_primes = []
    for p in primes():
        small_primes.append(p)
        primorial = reduce(mul, small_primes)
        wheel = [ i
                  for i in xrange(1, primorial+1)
                  if all(imap(lambda p: i % p, small_primes)) ]
        yield (primorial, wheel)

def roll_wheel(primorial, wheel, roots, start):
    skips = [ (wheel[(i + 1) % len(wheel)] - wheel[i]) % primorial
              for i in xrange(len(wheel)) ]
    if skips == [0]:
        skips = [1]
    start_index = wheel.index(start % primorial)
    wheel = frozenset(wheel)

    old_roots = set()
    for root in roots.iterkeys():
        if root % primorial not in wheel:
            old_roots.add(root)
    for root in sorted(old_roots):
        del roots[root]
    del old_roots

    p = start
    for incr in drop(start_index, cycle(skips)):
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
        p += incr

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
        for p in take(index+1, simple()):
            roots[p**2] = p
            yield p
    return chain(init(), roll_wheel(primorial, wheel, roots, nth(index+1, simple())))



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
