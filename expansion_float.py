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

# Adapted from https://www.cs.cmu.edu/~quake/robust.html (Shewchuk)
# http://perso.ens-lyon.fr/jean-michel.muller/ASAP2010-a.pdf (Muller)
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.55.3546&rep=rep1&type=pdf (Priest) (also available at the Shewchuk link)

# TODO: consistent naming

from __future__ import division

from sys import float_info
from itertools import chain, repeat, islice, imap
from numbers import Real, Rational
from collections import Iterable
from operator import neg
from math import trunc

import extended_float


def merge_iters(iter_a, iter_b,
                _chain=chain, _repeat=repeat):
    """
yields the items of iter_a and iter_b in order of nondecreasing
magnitude, assuming iter_a and iter_b also yield their values in that
order
"""
    sentinel = object()
    iter_a = _chain(iter_a, _repeat(sentinel))
    iter_b = _chain(iter_b, _repeat(sentinel))
    a = next(iter_a)
    b = next(iter_b)
    while a is not sentinel and b is not sentinel:
        if abs(a) <= abs(b):
            yield a
            a = next(iter_a)
        else:
            yield b
            b = next(iter_b)
    while a is not sentinel:
        yield a
        a = next(iter_a)
    while b is not sentinel:
        yield b
        b = next(iter_b)
    raise StopIteration

def two_sum(a, b,
            _add=extended_float.add,
            _sub=extended_float.sub):
    """returns the sum and error"""
    x = _add(a, b)
    b_virtual = _sub(x, a)
    a_virtual = _sub(x, b_virtual)
    b_roundoff = _sub(b, b_virtual)
    a_roundoff = _sub(a, a_virtual)
    y = _add(a_roundoff, b_roundoff)
    return (x, y)

def fast_two_sum(a, b,
                 _add=extended_float.add,
                 _sub=extended_float.sub):
    """returns the sum and error, provided that abs(a) >= abs(b)"""
    x = _add(a, b)
    b_virtual = _sub(x, a)
    y = _sub(b, b_virtual)
    return (x, y)

def two_diff(a, b,
             _add=extended_float.add,
             _sub=extended_float.sub):
    """returns difference and error"""
    x = _sub(a, b)
    b_virtual = _sub(a, x)
    a_virtual = _add(x, b_virtual)
    b_roundoff = _sub(b_virtual, b)
    a_roundoff = _sub(a, a_virtual)
    y = _add(a_roundoff, b_roundoff)
    return (x, y)

def grow_expansion(e, b,
                   _two_sum=two_sum):
    """returns the sum of expansion e and scalar b"""
    h = [ None ] * (len(e) + 1)
    q = b
    i = 0
    for e_i in e:
        q, h_i = _two_sum(q, e_i)
        if h_i:
            h[i] = h_i
            i += 1
    if q:
        h[i] = q
        i += 1
    del h[i:]
    return h

def expansion_sum(e, f,
                  _grow_expansion=grow_expansion):
    """
returns the sum of expansions e and f
if e has n components and f has m components, operates in O(m*n)
"""
    for f_i in f:
        e = _grow_expansion(e, f_i)
    return e

def fast_expansion_sum(e, f,
                       _merge_iters=merge_iters,
                       _two_sum=two_sum):
    """
returns the sum of expansions e and f
if e has n components and f has m components, operates in O(m+n)
only operates properly on systems with round-to-even behavior
"""
    g = _merge_iters(iter(e), iter(f))
    h = [ None ] * (len(e) + len(f))
    try:
        q = next(g)
    except StopIteration:
        return h # empty list
    i = 0
    for g_i in g:
        q, h_i = _two_sum(g_i, q)
        if h_i:
            h[i] = h_i
            i += 1
    if q:
        h[i] = q
        i += 1
    del h[i:]
    return h

def linear_expansion_sum(e, f,
                         _merge_iters=merge_iters,
                         _two_sum=two_sum,
                         _fast_two_sum=fast_two_sum):
    """
returns the sum of expansions e and f
if e has n components and f has m components, operates in O(m+n)
"""
    g = _merge_iters(iter(e), iter(f))
    h = [ None ] * (len(e) + len(f))
    try:
        Q, q = _two_sum(next(g), next(g))
    except StopIteration:
        return h # empty list
    i = 0
    for g_i in g:
        R, h_i = _fast_two_sum(g_i, q)
        if h_i:
            h[i] = h_i
            i += 1
        Q, q = _two_sum(Q, R)
    if q:
        h[i] = q
        i += 1
    if Q:
        h[i] = Q
        i += 1
    del h[i:]
    return h

def split(a, s,
          _mul=extended_float.mul,
          _sub=extended_float.sub):
    """returns the upper s bits, and remaining bits of a"""
    c = _mul((1<<s) + 1, a)
    a_big = _sub(c, a)
    a_hi = _sub(c, a_big)
    a_lo = _sub(a, a_hi)
    return (a_hi, a_lo)

def two_product(a, b,
                _mul=extended_float.mul,
                _sub=extended_float.sub,
                _split=split,
                _mant_dig=float_info.mant_dig):
    """returns the product and error"""
    x = _mul(a, b)
    a_hi, a_lo = _split(a, _mant_dig)
    b_hi, b_lo = _split(b, _mant_dig)
    err = _sub(_sub(_sub(x,
                         _mul(a_hi, b_hi)),
                    _mul(a_lo, b_hi)),
               _mul(a_hi, b_lo))
    y = _mul(_mul(a_lo, b_lo), err)
    return (x, y)

def scale_expansion(e, b,
                    _two_sum=two_sum,
                    _fast_two_sum=fast_two_sum,
                    _two_product=two_product):
    """returns the product of expansion e and scalar b"""
    h = [ None ] * (2*len(e))
    e_it = iter(e)
    i = 0
    try:
        q, h_i = _two_product(next(e_it), b)
    except StopIteration:
        return h # empty list
    if h_i:
        h[i] = h_i
        i += 1
    for e_i in e_it:
        T, t = _two_product(e_i, b)
        Q, h_i = _two_sum(q, t)
        if h_i:
            h[i] = h_i
            i += 1
        q, h_i = _fast_two_sum(T, Q)
        if h_i:
            h[i] = h_i
            i += 1
    if q:
        h[i] = q
        i += 1
    del h[i:]
    return h

def distill(it,
            _fast_expansion_sum=fast_expansion_sum):
    """returns the sum of expansions yielded by iterator it"""
    stack = []
    _push = stack.append
    _pop = stack.pop
    for i, e in enumerate(it):
        while i & 1:
            e = _fast_expansion_sum(e, _pop())
            i >>= 1
        _push(e)
    return reduce(_fast_expansion_sum, reversed(stack), [])

def expansion_product(e, f,
                      _distill=distill,
                      _imap=imap,
                      _scale_expansion=scale_expansion,
                      _repeat=repeat):
    """
returns the product of expansions e and f
uses a distillation tree of partial products
"""
    return _distill(_imap(_scale_expansion, _repeat(e), f))

def compress(e,
             _fast_two_sum=fast_two_sum,
             _islice=islice):
    """
returns an expansion equal to e with a more compact form (fewer
components, more significant bits in each component, and no zero
components)
"""
    h = [ None ] * len(e)
    e_it = iter(reversed(e))
    b = -1
    try:
        Q = next(e_it)
    except StopIteration:
        return h # empty list
    for e_i in e_it:
        Q, q = _fast_two_sum(Q, e_i)
        if q:
            h[b] = Q
            b -= 1
            Q = q
    h[b] = Q
    t = 0
    for h_i in _islice(h, len(h)+b+1, len(h)):
        Q, q = _fast_two_sum(h_i, Q)
        if q:
            h[t] = q
            t += 1
    h[t] = Q
    del h[t+1:]
    return h

def esum(it, start=0):
    """
compute the exact sum of iterable it and number start, returns the
nearest float
"""
    return sum(distill(imap(lambda x: [x], chain([start], it))))

def negate(x,
           _neg=neg,
           _map=map):
    return _map(_neg, x)

def long_division(a, b,
                  _sum=extended_float.sum,
                  _div=extended_float.div,
                  _scale_expansion=scale_expansion,
                  _fast_expansion_sum=fast_expansion_sum):
    """
performs long division of expansions a and b. returns the quotient and
remainder
"""
    q = []
    _append = q.append
    b_s = _sum(b)
    r = a
    while abs(_sum(r)) >= epsilon:
        p = _div(r[-1], b_s)
        r = _fast_expansion_sum(r, _scale_expansion(b, -p))
        _append(p)
    q.reverse()
    return (q, r)

def expansion_abs(a, _negate=negate):
    if not a:
        return []
    if a[-1] < 0:
        return _negate(a)
    return a

def newton_raphson_division(a, b, epsilon=float_info.min,
                            _sum=extended_float.sum,
                            _div=extended_float.div,
                            _negate=negate,
                            _fast_expansion_sum=fast_expansion_sum,
                            _expansion_product=expansion_product,
                            _expansion_abs=expansion_abs):
    """
performs Newton-Raphson division of expansions a and b. returns the
quotient and remainder
"""
    r = b
    x = [ _div(1., _sum(r)) ]
    while True:
        t = _expansion_product(b, x)
        # t = filter(lambda t_i: abs(t_i) >= epsilon, t)
        r_next = _fast_expansion_sum([1.], _negate(t))
        t = _expansion_product(r_next, x)
        # t = filter(lambda t_i: abs(t_i) >= epsilon, t)
        x = _fast_expansion_sum(x, t)
        p = _sum(_fast_expansion_sum(_expansion_abs(r),
                                     _negate(_expansion_abs(r_next))))
        print "p =", p
        if p < epsilon:
            break
        x = filter(lambda x_i: abs(x_i) >= epsilon, x)
        r = r_next
    print _sum(_fast_expansion_sum([1.], _negate(_expansion_product(x, b))))


    r = a
    y = _expansion_product(r, x)
    while True:
        t = _expansion_product(b, y)
        # t = filter(lambda t_i: abs(t_i) >= epsilon, t)
        r_next = _fast_expansion_sum(a, _negate(t))
        t = _expansion_product(r, x)
        # t = filter(lambda t_i: abs(t_i) >= epsilon, t)
        y = _fast_expansion_sum(y, t)
        p = _sum(_fast_expansion_sum(_expansion_abs(r),
                                     _negate(_expansion_abs(r_next))))
        print "p =", p
        # if p < epsilon:
        #     break
        y = filter(lambda y_i: abs(y_i) >= epsilon, y)
        r = r_next
    print _sum(_fast_expansion_sum(a, _negate(_expansion_product(y, b))))

    return (y, r)

def gcd(a, b,
        _newton_raphson_division=newton_raphson_division,
        _expansion_product=expansion_product,
        _negate=negate,
        _fast_expansion_sum=fast_expansion_sum):
    """
returns the greatest *REPRESENTABLE* divisor of expansions a and b
this is useful for canonicalizing ratios
"""
    while b:
        quot, rem = _newton_raphson_division(a, b)
        print "quot =", quot
        print "rem =", rem
        if not _fast_expansion_sum(rem, _negate(a)):
            # it is possible for a % b == a and b % a == b . In this
            # case, we cannot make progress.
            print "stuck"
            return [1.]
        a = b
        b = rem
    return a



from fluid import FluidManager, fluid_let

_epsilon_manager = FluidManager(epsilon=float_info.min)
def epsilon(value):
    return fluid_let(_epsilon_manager, epsilon=value)



class ExpansionFloat(Real, tuple):
    """
Exactly represents a float using expansions. Arithmetic is performed
exactly, within the representable range of the underlying float's
exponent.
"""

    def __new__(cls, initial_value=0):
        if isinstance(initial_value, Iterable):
            return super(ExpansionFloat, cls).__new__(cls, initial_value)
        elif isinstance(initial_value, Real):
            return super(ExpansionFloat, cls).__new__(cls, [initial_value])
        else:
            tiv = type(initial_value)
            raise TypeError("Cannot convert object of type %s to %s" %
                            (tiv.__module__ + '.' + tiv.__name__,
                             cls.__module__ + '.' + cls.__name__))


    def __repr__(self):
        cls = type(self)
        name = cls.__module__ + '.' + cls.__name__
        return name + '(' + repr(tuple(self)) + ')'


    def compress(self):
        return type(self)(compress(self))
    def __float__(self):
        return sum(self)
    def __trunc__(self):
        ret = 0
        for i in reversed(self):
            if abs(i) < 1:
                break
            ret += int(i)
        return ret
    @property
    def sign(self):
        if len(self):
            if self[-1] > 0:
                return 1
            else:
                return -1
        else:
            return 0

    def __neg__(self):
        return type(self)(imap(neg, self))
    def __pos__(self):
        return self
    def __abs__(self):
        if self.sign < 0:
            return -self
        else:
            return self

    def __lt__(self, other):
        return (self - other).sign < 0
    def __le__(self, other):
        return (self - other).sign <= 0
    def __eq__(self, other):
        return (self - other).sign == 0
    # __ne__ falls back to numbers.Complex
    def __gt__(self, other):
        return (self - other).sign > 0
    def __ge__(self, other):
        return (self - other).sign >= 0

    def __hash__(self):
        try:
            return self.hash_value
        except AttributeError:
            if not self:
                self.hash_value = hash(0)
            else:
                canon = self.compress()
                if len(canon) == 1:
                    self.hash_value = hash(canon[0])
                else:
                    if self[0].is_integer():
                        self.hash_value = hash(trunc(self))
                    else:
                        self.hash_value = hash(tuple(canon))
            return hash(self)

    def __add__(self, other):
        if isinstance(other, ExpansionFloat):
            return type(self)(fast_expansion_sum(self, other))
        else:
            return self + type(self)(other)
    def __radd__(self, other):
        return self + other

    # __sub__ and __rsub__ fall back to numbers.Complex

    def __mul__(self, other):
        if isinstance(other, ExpansionFloat):
            return type(self)(expansion_product(self, other))
        else:
            return self * type(self)(other)
    def __rmul__(self, other):
        return self * other

    def __divmod__(self, other):
        if isinstance(other, ExpansionFloat):
            quot, rem = newton_raphson_division(self, other)
            return (type(self)(quot), type(self)(rem))
        else:
            return divmod(self, type(self)(other))
    def __rdivmod__(self, other):
        if isinstance(other, ExpansionFloat):
            quot, rem = newton_raphson_division(other, self)
            return (type(self)(quot), type(self)(rem))
        else:
            return divmod(type(self)(other), self)
    def __div__(self, other):
        return self / other
    def __rdiv__(self, other):
        return other / self
    def __truediv__(self, other):
        return divmod(self, other)[0]
    def __rtruediv__(self, other):
        return divmod(other, self)[0]
    def __floordiv__(self, other):
        # TODO: run Newton-Raphson for only enough steps to get an int
        return trunc(self / other)
    def __rfloordiv__(self, other):
        return trunc(other / self)

    def __mod__(self, other):
        return divmod(self, other)[1]
    def __rmod__(self, other):
        return divmod(other, self)[1]

    def __pow__(self, exponent, modulus):
        raise NotImplementedError
    def __rpow__(self, base, modlulus):
        raise NotImplementedError


class ProjectiveExpansionFloat(Rational):
    """
Exactly represents a rational number using ExpansionFloat's. You
cannot use normal ExpansionFloats for this because some
ExpansionFloats do not have representable reciprocals.

*WARNING*
Athough this class purports to be an instance of Rational,
ProjectiveExpansionFloat.numerator and
ProjectiveExpansionFloat.denominator are *NOT* in lowest terms (but
hash() and == will perform appropriate reductions). To obtain lowest
(representable) terms, use ProjectiveExpansionFloat.compress().
*WARNING*
"""
    __slots__ = ('numerator', 'denominator', 'hash_value')

    def __init__(self, numerator=0, denominator=None):
        if denominator is None:
            if isinstance(numerator, ProjectiveExpansionFloat):
                self.numerator = numerator.numerator
                self.denominator = numerator.denominator
            else:
                self.numerator = ExpansionFloat(numerator)
                if denominator is None:
                    self.denominator = ExpansionFloat(1)
                else:
                    self.denominator = ExpansionFloat(denominator)
        else:
            denominator = ExpansionFloat(denominator)
            if not denominator:
                raise ZeroDivisionError
            numerator = ExpansionFloat(numerator)
            self.numerator = numerator
            self.denominator = denominator

    def __repr__(self):
        cls = type(self)
        name = cls.__module__ + '.' + cls.__name__
        return name + '(' + repr(self.numerator) + ', ' + repr(self.denominator) + ')'

    def compress(self):
        numerator = self.numerator
        print "numerator =", numerator
        denominator = self.denominator
        print "denominator =", denominator
        divisor = gcd(numerator, denominator)
        print "divisor =", divisor
        numerator /= divisor
        print "numerator / divisor =", numerator
        denominator /= divisor
        print "denominator / divisor =", denominator
        numerator = numerator.compress()
        denominator = denominator.compress()
        if denominator.sign < 0:
            return type(self)(-numerator, -denominator)
        else:
            return type(self)(numerator, denominator)
    def to_affine(self):
        return self.numerator / self.denominator
    def __float__(self):
        return float(self.to_affine())
    def __trunc__(self):
        return trunc(self.to_affine())
    @property
    def sign(self):
        return self.numerator.sign * self.denominator.sign
    def __nonzero__(self):
        return self.numerator.sign != 0

    def __neg__(self):
        return type(self)(-self.numerator, self.denominator)
    def __pos__(self):
        return self
    def __abs__(self):
        if self.sign < 0:
            return -self
        else:
            return self

    def __lt__(self, other):
        return (self - other).sign < 0
    def __le__(self, other):
        return (self - other).sign <= 0
    def __eq__(self, other):
        return (self - other).sign == 0
    # __ne__ falls back to numbers.Complex
    def __gt__(self, other):
        return (self - other).sign > 0
    def __ge__(self, other):
        return (self - other).sign >= 0

    def __hash__(self):
        try:
            return self.hash_value
        except AttributeError:
            canon = self.compress()
            if canon.denominator == 1:
                self.hash_value = hash(canon.numerator)
            else:
                self.hash_value = hash((canon.numerator,
                                        canon.denominator))
            return hash(self)

    def __add__(self, other):
        if isinstance(other, ProjectiveExpansionFloat):
            return type(self)(self.numerator * other.denominator
                              + other.numerator * self.denominator,
                              self.denominator * other.denominator)
        else:
            return self + type(self)(other)
    def __radd__(self, other):
        return self + other

    # __sub__ and __rsub__ fall back to numbers.Complex

    def __mul__(self, other):
        if isinstance(other, ProjectiveExpansionFloat):
            return type(self)(self.numerator * other.numerator,
                              self.denominator * other.denominator)
        else:
            return self * type(self)(other)
    def __rmul__(self, other):
        return self * other

    # __divmod__ and __rdivmod__ fall back to numbers.Real

    def __div__(self, other):
        return self / other
    def __rdiv__(self, other):
        return other / self
    def __truediv__(self, other):
        if isinstance(other, ProjectiveExpansionFloat):
            return type(self)(self.numerator * other.denominator,
                              self.denominator * other.numerator)
        else:
            return self / type(self)(other)
    def __rtruediv__(self, other):
        if isinstance(other, ProjectiveExpansionFloat):
            return type(self)(other.numerator * self.denominator,
                              other.denominator * self.numerator)
        else:
            return type(self)(other) / self
    def __floordiv__(self, other):
        return trunc(self / other)
    def __rfloordiv__(self, other):
        return trunc(other / self)

    def __mod__(self, other):
        if isinstance(other, ProjectiveExpansionFloat):
            return self - other * (self // other)
        else:
            return self % type(self)(other)
    def __rmod__(self, other):
        if isinstance(other, ProjectiveExpansionFloat):
            return other - self * (other // self)
        else:
            return type(self)(other) % self

    def __pow__(self, exponent, modulus):
        raise NotImplementedError
    def __rpow__(self, base, modulus):
        raise NotImplementedError

__all__ = ('esum', 'epsilon', 'ExpansionFloat', 'ProjectiveExpansionFloat')
