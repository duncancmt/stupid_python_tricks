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

from itertools import *
from fractions import gcd
from operator import mul, itemgetter
from bisect import bisect_left
from numbers import Integral


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


    def _index_unsafe(self, elem):
        cycle, raw_spoke = divmod(elem, self.modulus)
        spoke = bisect_left(self.spokes, raw_spoke)
        return (cycle, spoke)


    def index(self, elem):
        if elem not in self:
            raise IndexError("%d is not in %s" % (elem, type(self).__name__))
        return self._index_unsafe(elem)


    def __getitem__(self, elem):
        if isinstance(elem, Integral):
            cycle, spoke = self.index(elem)
        else:
            cycle, spoke = elem
        return cycle*self.modulus + self.spokes[spoke]


    def __contains__(self, elem):
        return gcd(elem, self.modulus) == 1


    def __iter__(self):
        spokes = self.spokes
        modulus = self.modulus
        for i in count(1):
            for j in spokes:
                yield i*modulus + j


    def _advance_hazard(self, hazard, sieve):
        modulus = self.modulus
        spokes = self.spokes
        prime, cycle, spoke = sieve[hazard]
        # assert hazard not in self \
        #     or hazard == prime * (cycle*modulus + spokes[spoke])
        next_hazard = hazard
        while next_hazard in sieve:
            spoke += 1
            cycle_incr, spoke = divmod(spoke, len(spokes))
            cycle += cycle_incr
            next_hazard = prime * (cycle*modulus + spokes[spoke])
        # assert next_hazard in self
        del sieve[hazard]
        sieve[next_hazard] = (prime, cycle, spoke)


    def _update_sieve(self, sieve):
        to_delete = set()
        to_advance = set()
        for hazard, (prime, _, __) in sieve.iteritems():
            if prime not in self:
                to_delete.add(hazard)
            elif hazard in self:
                cycle, spoke = self.index(hazard // prime)
                sieve[hazard] = (prime, cycle, spoke)
            else:
                cycle, spoke = self._index_unsafe(hazard // prime)
                # it's OK to not use clock arithmetic for spoke here
                # because the very next thing we're going to do to it
                # is add 1
                sieve[hazard] = (prime, cycle, spoke-1)
                to_advance.add(hazard)
        for hazard in to_delete:
            del sieve[hazard]
        for hazard in sorted(to_advance,
                             key=lambda hazard: sieve[hazard][0]):
            self._advance_hazard(hazard, sieve)
        # assert len(frozenset(imap(itemgetter(0), \
        #                           sieve.itervalues()))) \
        #        == len(sieve)
        # assert all(imap(lambda hazard: hazard in self, sieve.iterkeys()))


    def roll(self, cycles, sieve):
        if cycles is None:
            candidate_stream = iter(self)
        else:
            candidate_stream = iter(take(len(self.spokes)*cycles, self))

        self._update_sieve(sieve)

        for candidate in candidate_stream:
            if candidate in sieve:
                self._advance_hazard(candidate, sieve)
            else:
                prime = candidate
                cycle, spoke = self.index(candidate)
                sieve[prime**2] = (candidate, cycle, spoke)
                yield prime
            # assert all(imap(lambda h: h > candidate, sieve.iterkeys()))


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
    for p in takewhile(lambda p: p < w.modulus, simple()):
        if p in w:
            for q in dropwhile(lambda q: q < p,
                               takewhile(lambda q: q < w.modulus,
                                         simple())):
                hazard = p*q
                if hazard > w.modulus and hazard in w:
                    sieve[hazard] = (p, None, None)
                    break

    return chain(takewhile(lambda p: p < w.modulus, simple()),
                 w.roll(None, sieve))



def variable_wheel():
    sieve = {}
    return chain.from_iterable( ( wheel.roll(prime-1, sieve)
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
