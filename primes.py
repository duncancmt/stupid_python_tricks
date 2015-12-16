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
    class Spokes(object):
        def __init__(self, iterator, length, last):
            self.iterator = take(length, iterator)
            self.length = length
            self.last = last
            self.cache = []

        def _fill_cache(self, n):
            n = n + len(self) if n < 0 else n
            it = self.iterator
            try:
                while n >= len(self.cache):
                    self.cache.append(next(it))
            except StopIteration:
                raise IndexError("%s index out of range or iterator ended early" % type(self).__name__)

        def __len__(self):
            return self.length

        def __getitem__(self, key):
            self._fill_cache(key)
            return self.cache[key]

        def index(self, needle):
            left = 0
            left_value = self[left]
            right = self.length-1
            right_value = self.last
            while True:
                guess = ((right - left) * max(needle - left_value, 0) \
                         // max(right_value - left_value, 1)) + left
                guess_value = self[guess]
                if guess_value == needle:
                    # base case; needle is found
                    return guess
                elif guess_value < needle:
                    left = guess + 1
                    left_value = self[left]
                elif guess-1 < 0 or self[guess-1] < needle:
                    # base case; needle isn't present; return the
                    # index of the next-largest element
                    return guess
                else:
                    right = guess - 1
                    right_value = self[right]



    def __init__(self, smaller, prime):
        if smaller is None and prime is None:
            self.modulus = 1
            self.spokes = self.Spokes((1,), 1, 1)
        else:
            self.modulus = smaller.modulus * prime
            self.spokes = self.Spokes(ifilter(lambda x: x % prime,
                                              smaller),
                                      len(smaller.spokes)*(prime-1),
                                      self.modulus)


    def _index_unsafe(self, elem):
        cycle, raw_spoke = divmod(elem, self.modulus)
        spoke = self.spokes.index(raw_spoke)
        return (cycle, spoke)


    def index(self, elem):
        ret = self._index_unsafe(elem)
        if self[ret] != elem:
            raise IndexError("%d is not in %s" % (elem, type(self).__name__))
        return ret


    def __getitem__(self, elem):
        cycle, spoke = elem
        return cycle*self.modulus + self.spokes[spoke]


    def __contains__(self, elem):
        return gcd(elem, self.modulus) == 1


    def __iter__(self):
        spokes = self.spokes
        modulus = self.modulus
        for i in count():
            for j in spokes:
                yield i*modulus + j


    def _advance_hazard(self, hazard, sieve):
        modulus = self.modulus
        spokes = self.spokes
        prime, cycle, spoke = sieve[hazard]
        # assert hazard not in self \
        #     or hazard == prime * self[(cycle, spoke)]
        next_hazard = hazard
        while next_hazard in sieve:
            spoke += 1
            cycle_incr, spoke = divmod(spoke, len(spokes))
            cycle += cycle_incr
            next_hazard = prime * self[(cycle, spoke)]
        # assert next_hazard in self
        del sieve[hazard]
        sieve[next_hazard] = (prime, cycle, spoke)


    def _update_sieve(self, sieve):
        if sieve is None:
            sieve = {}
            for p in takewhile(lambda p: p < self.modulus, simple()):
                if p in self:
                    for q in dropwhile(lambda q: q < p,
                                       takewhile(lambda q: q < self.modulus,
                                                 simple())):
                        hazard = p*q
                        if hazard > self.modulus and hazard in self:
                            sieve[hazard] = (p, None, None)
                            break

        to_delete = set()
        to_advance = set()
        for hazard, (prime, _, __) in sieve.iteritems():
            if prime not in self:
                to_delete.add(hazard)
            elif hazard in self:
                cycle, spoke = self._index_unsafe(hazard // prime)
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
        return sieve


    def roll(self, cycles, sieve=None):
        sieve = self._update_sieve(sieve)

        candidate_stream = drop(len(self.spokes), self)
        if cycles is not None:
            candidate_stream = take(len(self.spokes)*cycles, candidate_stream)

        for candidate in candidate_stream:
            if candidate in sieve:
                self._advance_hazard(candidate, sieve)
            else:
                cycle, spoke = self._index_unsafe(candidate)
                sieve[candidate**2] = (candidate, cycle, spoke)
                yield candidate
            # assert all(imap(lambda h: h > candidate, sieve.iterkeys()))


    class __metaclass__(type):
        def __iter__(cls):
            last = cls(None, None)
            yield last
            for prime in simple():
                last = cls(last, prime)
                yield last


    def __repr__(self):
        return "<%s.%s with modulus %d>" % \
            (__name__, type(self).__name__, self.modulus)



def fixed_wheel(index):
    w = nth(index, Wheel)
    return chain(takewhile(lambda p: p < w.modulus, simple()),
                 w.roll(None))



def variable_wheel():
    sieve = {}
    return chain.from_iterable( ( wheel.roll(prime-1, sieve)
                                  for wheel, prime in izip(Wheel, simple()) ) )



def _check_fixed(index, up_to):
    try:
        import pyprimes.sieves
        good_stream = pyprimes.sieves.best_sieve()
    except ImportError:
        good_stream = simple()
    for i, (a, b) in enumerate(take(up_to,
                                    izip(fixed_wheel(index),
                                         good_stream))):
        if a != b:
            return i

def _check_variable(up_to):
    try:
        import pyprimes.sieves
        good_stream = pyprimes.sieves.best_sieve()
    except ImportError:
        good_stream = simple()
    for i, (a, b) in enumerate(take(up_to,
                                    izip(variable_wheel(),
                                         good_stream))):
        if a != b:
            return i


if __name__ == '__main__':
    import sys
    print nth(int(sys.argv[1]), variable_wheel())
