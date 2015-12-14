# This file is part of stupid_python_tricks written by Duncan Townsend.
#
# stupid_python_tricks is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# stupid_python_tricks is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with stupid_python_tricks.  If not, see <http://www.gnu.org/licenses/>.

from itertools import ifilter, islice, izip, count, chain, takewhile
from fractions import gcd
from operator import mul
from bisect import bisect_left

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
    return islice(stream, None, n, None)


def drop(n, stream):
    return islice(stream, n, None, None)


def nth(n, stream):
    try:
        return next(drop(n, stream))
    except StopIteration:
        raise IndexError("Can't get element off the end of generator")



class Wheel(object):
    def __init__(self, seeds):
        self.seeds = tuple(seeds)
        self.modulus = reduce(mul, self.seeds, 1)
        self.spokes = tuple(candidate
                            for candidate in xrange(1, self.modulus+1)
                            if candidate in self)


    def roll(self, start=None):
        modulus = self.modulus
        spokes = self.spokes

        if start is None:
            start_cycle, start_spoke = 1, 0
        else:
            start_cycle, start_spoke = divmod(start, modulus)
            start_spoke = bisect_left(spokes, start_spoke)

        start_cycle *= modulus
        for i in xrange(start_spoke, len(spokes)):
            yield start_cycle + spokes[i]
        for cycle in count(modulus + start_cycle, modulus):
            for spoke in spokes:
                yield cycle + spoke


    def _advance_hazard(self, hazard, sieve):
        prime, it = sieve.pop(hazard)
        hazard = prime * next(it)
        while hazard in sieve:
            hazard = prime * next(it)
        # assert hazard in self
        sieve[hazard] = (prime, it)


    def _update_sieve(self, sieve):
        to_delete = set()
        to_advance = set()
        for hazard, (prime, _) in sieve.iteritems():
            if prime not in self:
                to_delete.add(hazard)
            else:
                sieve[hazard] = (prime, self.roll(hazard // prime))
                to_advance.add(hazard)
        for hazard in to_delete:
            del sieve[hazard]
        for hazard in sorted(to_advance):
            self._advance_hazard(hazard, sieve)


    def steer(self, cycles, sieve):
        if cycles is None:
            candidate_stream = iter(self)
        else:
            candidate_stream = iter(take(len(self.spokes)*cycles, self))

        self._update_sieve(sieve)

        for candidate in candidate_stream:
            if candidate in sieve:
                self._advance_hazard(candidate, sieve)
            else:
                it = self.roll(candidate)
                sieve[candidate*next(it)] = (candidate, it)
                yield candidate


    def __iter__(self):
        return self.roll()


    def __contains__(self, elem):
        return gcd(elem, self.modulus) == 1


    class __metaclass__(type):
        def __iter__(cls):
            primes = []
            yield cls(primes)
            for prime in simple():
                primes.append(prime)
                yield cls(primes)


    def __repr__(self):
        return "%s.%s(%s)" % \
            (__name__, type(self).__name__, self.seeds)



def fixed_wheel(index):
    """A very fast wheel+sieve prime generator.

    Adapted from http://stackoverflow.com/q/2211990 with an adjustable
    wheel size.
    """

    # precomputation of the wheel
    w = nth(index, Wheel)

    # populate the sieve
    sieve = {}
    # TODO: I'm not sure what the time complexity of this double loop
    # is, but I'm sure it's terrible
    for p in takewhile(lambda p: p < w.modulus, simple()):
        for q in takewhile(lambda q: q <= p, simple()):
            sieve[p*q] = (q, None)
    return chain(takewhile(lambda p: p < w.modulus, simple()),
                 w.steer(None, sieve))



def variable_wheel():
    sieve = {}
    return chain.from_iterable( ( wheel.steer(prime-1, sieve)
                                  for wheel, prime in izip(Wheel, simple()) ) )



def _check_fixed(index, up_to):
    for i, (a, b) in enumerate(take(up_to, izip(fixed_wheel(index), simple()))):
        if a != b:
            return i

def _check_variable(up_to):
    for i, (a, b) in enumerate(take(up_to, izip(variable_wheel(), simple()))):
        if a != b:
            return i


if __name__ == '__main__':
    import sys
    print nth(int(sys.argv[1]), variable_wheel())
