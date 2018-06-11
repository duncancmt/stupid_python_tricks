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



from __future__ import division

import math
from sys import float_info
from numbers import Real
from collections import namedtuple


def normalize(m, e,
              _frexp=math.frexp):
    if m:
        m, e_prime = _frexp(m)
        e += e_prime
        return (m, e)
    else:
        return (0., 0L)

def me_add((a_m, a_e), (b_m, b_e),
           _shift_limit=float_info.mant_dig+1,
           _ldexp=math.ldexp,
           _normalize=normalize):
    if (a_e < b_e and b_m) or not a_m:
        a_m, b_m = b_m, a_m
        a_e, b_e = b_e, a_e
    s = (a_e - b_e)
    if s > _shift_limit:
        ret = _normalize(a_m + _ldexp(b_m, -s), a_e)
        assert ret == (a_m, a_e), (_ldexp(a_m, a_e), _ldexp(b_m, b_e), _ldexp(*_normalize(a_m + _ldexp(b_m, -s), a_e)))
        return (a_m, a_e)
    return _normalize(a_m + _ldexp(b_m, -s), a_e)

def me_sub(a, (b_m, b_e),
        _me_add=me_add):
    return _me_add(a, (-b_m, b_e))

def me_mul((a_m, a_e), (b_m, b_e),
           _normalize=normalize):
    return _normalize(a_m * b_m, a_e + b_e)

def me_div((a_m, a_e), (b_m, b_e),
           _normalize=normalize):
    return _normalize(a_m / b_m, a_e - b_e)

def me_trunc((m, e),
             _min_exp=float_info.min_exp,
             _max_exp=float_info.max_exp,
             _ldexp=math.ldexp,
             _trunc=math.trunc,
             _frexp=math.frexp):
    if e < _min_exp:
        return (0., 0L)
    if e <= _max_exp:
        return _frexp(_trunc(_ldexp(m, e)))
    else:
        return (m, e)

def me_ceil((m, e),
            _min_exp=float_info.min_exp,
            _max_exp=float_info.max_exp,
            _ldexp=math.ldexp,
            _ceil=math.ceil,
            _frexp=math.frexp):
    if e < _min_exp:
        if m > 0:
            return (0.5, 1L)
        else:
            return (0., 0L)
    elif e <= _max_exp:
        return _frexp(_ceil(_ldexp(m, e)))
    else:
        return (m, e)

def me_floor((m, e),
             _min_exp=float_info.min_exp,
             _max_exp=float_info.max_exp,
             _ldexp=math.ldexp,
             _floor=math.floor,
             _frexp=math.frexp):
    if e < _min_exp:
        if m >= 0:
            return (0., 0L)
        else:
            return (-0.5, 1L)
    elif e <= _max_exp:
        return _frexp(_floor(_ldexp(m, e)))
    else:
        return (m, e)

def me_fmod(a, b,
            _me_div=me_div,
            _me_trunc=me_trunc,
            _me_mul=me_mul,
            _me_sub=me_sub):
    n = _me_div(a, b)
    n = _me_trunc(n)
    r = _me_mul(n, b)
    return _me_sub(a, r)

def me_mod(a, b,
           _me_fmod=me_fmod,
           _me_add=me_add):
    ret = _me_fmod(a, b)
    if a[0] * b[0] < 0.:
        ret = _me_add(ret, b)
    return ret



class ExtendedExponentFloat(Real, namedtuple('ExtendedExponentFloatBase', ('mantissa', 'exponent'))):
    """
Represents a float with no range restrictions on the exponent. The
precision of the mantissa is the same as the underlying float
implementation.

All operations (including the constructor) will return native floats
when the exponent is in non-subnormal range.
"""

    def __new__(cls, mantissa=0, exponent=None,
                _frexp=math.frexp,
                _ldexp=math.ldexp,
                _normalize=normalize,
                _min_exp=float_info.min_exp,
                _max_exp=float_info.max_exp):
        if exponent is None:
            if isinstance(mantissa, cls):
                return cls.__new__(cls, mantissa.mantissa, mantissa.exponent)
            else:
                return cls.__new__(cls, *_frexp(float(mantissa)))
        else:
            mantissa, exponent = _normalize(float(mantissa), long(exponent))
            if exponent >= _min_exp and exponent <= _max_exp:
                ret = _ldexp(mantissa, exponent)
            else:
                ret = super(ExtendedExponentFloat, cls).__new__(cls, mantissa, exponent)
            assert cls.check(ret, mantissa, exponent), \
                "%%s is not the correct representation of %%.%df * 2 ** %%d" \
                  % (float_info.dig,) \
                  % (repr(ret) if isinstance(ret, ExtendedExponentFloat) else "%%.%df" % (float_info.dig,) % ret, mantissa, exponent)
            return ret
    @classmethod
    def check(cls, x, mantissa, exponent,
              _frexp=math.frexp, _ldexp=math.ldexp,
              _min=float_info.min, _max=float_info.max):
        if isinstance(x, ExtendedExponentFloat):
            try:
                return not cls.check(_ldexp(x.mantissa, x.exponent), mantissa, exponent)
            except OverflowError:
                return True
        else:
            return (not x or abs(x) >= _min) \
                and abs(x) <= _max \
                and _frexp(x) == (mantissa, exponent)


    def __repr__(self):
        cls = type(self)
        name = cls.__module__ + '.' + cls.__name__
        return name \
            + '(' \
            + ", ".join( field + '=' + repr(getattr(self, field))
                       for field in self._fields) \
            + ')'

    def __float__(self, _ldexp=math.ldexp):
        return _ldexp(self.mantissa, self.exponent)
    def __trunc__(self,
                  _me_trunc=me_trunc,
                  _mant_dig=float_info.mant_dig,
                  _ldexp=math.ldexp):
        mantissa, exponent = _me_trunc(self)
        if exponent > _mant_dig:
            return long(_ldexp(mantissa, _mant_dig)) << (exponent - _mant_dig)
        else:
            return long(_ldexp(mantissa, exponent))
    def __nonzero__(self):
        return True
    @property
    def sign(self):
        if self.mantissa > 0:
            return 1
        elif self.mantissa == 0:
            return 0
        else:
            return -1
    @property
    def trunc(self, _me_trunc=me_trunc):
        return type(self)(*_me_trunc(self))
    @property
    def ceil(self, _me_ceil=me_ceil):
        return type(self)(*_me_ceil(self))
    @property
    def floor(self, _me_floor=me_floor):
        return type(self)(*_me_floor(self))

    def __lt__(self, other):
        difference = self - other
        if isinstance(difference, ExtendedExponentFloat):
            return difference.sign < 0
        else:
            return difference < 0
    def __le__(self, other):
        difference = self - other
        if isinstance(difference, ExtendedExponentFloat):
            return difference.sign <= 0
        else:
            return difference <= 0
    def __eq__(self, other):
        return not self - other
    # __ne__ falls back to numbers.Complex
    def __gt__(self, other):
        return not self <= other
    def __ge__(self, other):
        return not self < other

    def __neg__(self):
        return type(self)(-self.mantissa, self.exponent)
    def __pos__(self):
        return self
    def __abs__(self):
        if self.mantissa < 0:
            return -self
        else:
            return self

    def __add__(self, other, _me_add=me_add, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_add(self, other))
        elif isinstance(other, float):
            return cls(*_me_add(self, _frexp(other)))
        else:
            return self + cls(other)
    def __radd__(self, other):
        return self + other

    # __sub__ and __rsub__ fall back to numbers.Complex

    def __mul__(self, other, _me_mul=me_mul, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_mul(self, other))
        elif isinstance(other, float):
            return cls(*_me_mul(self, _frexp(other)))
        else:
            return self * cls(other)
    def __rmul__(self, other):
        return self * other

    # __divmod__ and __rdivmod__ fall back to numbers.Real

    def __div__(self, other):
        return self / other
    def __rdiv__(self, other):
        return other / self
    def __truediv__(self, other, _me_div=me_div, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_div(self, other))
        elif isinstance(other, float):
            return cls(*_me_div(self, _frexp(other)))
        else:
            return self / cls(other)
    def __rtruediv__(self, other, _me_div=me_div, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_div(other, self))
        elif isinstance(other, float):
            return cls(*_me_div(_frexp(other), self))
        else:
            return cls(other) / self
    def __floordiv__(self, other):
        return (self / other).floor
    def __rfloordiv__(self, other):
        return (other / self).floor

    def __mod__(self, other, _me_mod=me_mod, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_mod(self, other))
        elif isinstance(other, float):
            return cls(*_me_mod(self, _frexp(other)))
        else:
            return self % cls(other)
    def __rmod__(self, other, _me_mod=me_mod, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_mod(other, self))
        elif isinstance(other, float):
            return cls(*_me_mod(_frexp(other), self))
        else:
            return cls(other) % self

    def fmod(self, other, _me_fmod=me_fmod, _frexp=math.frexp):
        cls = type(self)
        if isinstance(other, ExtendedExponentFloat):
            return cls(*_me_fmod(self, other))
        elif isinstance(other, float):
            return cls(*_me_fmod(self, _frexp(other)))
        else:
            return self.fmod(cls(other))

    def __pow__(self, exponent, modulus):
        raise NotImplementedError
    def __rpow__(self, base, modulus):
        raise NotImplementedError

    @classmethod
    def add(cls, a, b,
            _min=float_info.min,
            _max=float_info.max,
            _frexp=math.frexp,
            _me_add=me_add):
        ret = a + b
        return ret # debug
        if isinstance(ret, float) \
           and (abs(ret) > _max or abs(ret) < _min):
            return cls(*_me_add(_frexp(a), _frexp(b)))
        else:
            return ret
    @classmethod
    def sub(cls, a, b,
            _min=float_info.min,
            _max=float_info.max,
            _frexp=math.frexp,
            _me_sub=me_sub):
        ret = a - b
        return ret # debug
        if isinstance(ret, float) \
           and (abs(ret) > _max or abs(ret) < _min):
            return cls(*_me_sub(_frexp(a), _frexp(b)))
        else:
            return ret
    @classmethod
    def mul(cls, a, b,
            _min=float_info.min,
            _max=float_info.max,
            _frexp=math.frexp,
            _me_mul=me_mul):
        ret = a * b
        return ret # debug
        if isinstance(ret, float) \
           and (abs(ret) > _max or abs(ret) < _min):
            return cls(*_me_mul(_frexp(a), _frexp(b)))
        else:
            return ret
    @classmethod
    def div(cls, a, b,
            _min=float_info.min,
            _max=float_info.max,
            _frexp=math.frexp,
            _me_div=me_div):
        ret = a / b
        return ret # debug
        if isinstance(ret, float) \
           and (abs(ret) > _max or abs(ret) < _min):
            return cls(*_me_div(_frexp(a), _frexp(b)))
        else:
            return ret
    @classmethod
    def mod(cls, a, b,
            _min=float_info.min,
            _max=float_info.max,
            _frexp=math.frexp,
            _me_mod=me_mod):
        ret = a % b
        return ret # debug
        if isinstance(ret, float) \
           and (abs(ret) > _max or abs(ret) < _min):
            return cls(*_me_mod(_frexp(a), _frexp(b)))
        else:
            return ret
    @classmethod
    def fmod(cls, a, b,
             _fmod=fmod,
             _min=float_info.min,
             _max=float_info.max,
             _frexp=math.frexp,
             _me_fmod=me_fmod):
        ret = _fmod(a, b)
        return ret # debug
        if isinstance(ret, float) \
           and (abs(ret) > _max or abs(ret) < _min):
            return cls(*_me_fmod(_frexp(a), _frexp(b)))
        else:
            return ret



add = ExtendedExponentFloat.add
sub = ExtendedExponentFloat.sub
mul = ExtendedExponentFloat.mul
div = ExtendedExponentFloat.div
mod = ExtendedExponentFloat.mod
fmod = ExtendedExponentFloat.fmod

trunc = math.trunc
def ceil(x, _ceil=math.ceil):
    if isinstance(x, float):
        return _ceil(x)
    elif isinstance(x, ExtendedExponentFloat):
        return x.ceil
    else:
        raise TypeError
def floor(x, _floor=math.floor):
    if isinstance(x, float):
        return _floor(x)
    elif isinstance(x, ExtendedExponentFloat):
        return x.floor
    else:
        raise TypeError
def sum(it, _add=add):
    return reduce(_add, it, 0.)
        


__all__ = ('ExtendedExponentFloat', 'add', 'sub', 'mul', 'div', 'mod', 'fmod', 'trunc', 'ceil', 'floor', 'sum')
