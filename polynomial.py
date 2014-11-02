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

from immutable import *
from itertools import *
from operator import *
from functools import cmp_to_key
from collections import Iterable, Mapping
from numbers import Real, Integral
from copy import copy,deepcopy

class Term(object):
    __metaclass__ = ImmutableEnforcerMeta
    __slots__ = ['__proper', '__lexicographic_key', '__vars', '__coeff', '__powers']
    convertable_types = (Real, basestring, Mapping, tuple)
    def __init__(self, *args):
        super(Term, self).__init__()
        coeff = [1] # stupid python scoping rules
        powers = dict()

        def put_var(var, power):
            if not isinstance(var, basestring):
                raise TypeError("Invalid variable name",var)
            if not isinstance(power, Real):
                raise TypeError("Invalid variable power",power)
            powers[var] = powers.get(var, 0) + power

        def put_arg(a):
            if isinstance(a, Term):
                coeff[0] *= a.coeff
                for (var, power) in a.powers.iteritems():
                    put_var(var, power)
            elif isinstance(a, Real):
                coeff[0] *= a # stupid python scoping rules
            elif isinstance(a, basestring):
                powers[a] = powers.get(a, 0) + 1
            elif isinstance(a, Mapping):
                for (var, power) in a.iteritems():
                    put_var(var, power)
            elif isinstance(a, tuple):
                put_var(*a)
            elif isinstance(a, Iterable):
                for a in a:
                    put_arg(a)
            else:
                raise TypeError("Invalid term element",a)

        for a in args:
            put_arg(a)
        self.coeff = coeff[0] # stupid python scoping rules
        if self.coeff == 0:
            powers = dict()
        self.trim_powers(powers)
        self.powers = ImmutableDict(powers)

    @staticmethod
    def trim_powers(powers):
        to_delete = []
        for var, power in powers.iteritems():
            if power == 0:
                to_delete.append(var)
        for var in to_delete:
            del powers[var]

    def __pow__(self, other):
        if not isinstance(other, Real):
            raise TypeError("Can only raise Terms to Real powers (not variable powers)")
        return type(self)(self.coeff ** other,
                          imap(lambda (var, power): (var, power*other),
                               self.powers.iteritems()))

    def __rmul__(self, other):
        return self * other
    def __mul__(self, other):
        if isinstance(other, self.convertable_types):
            return self * type(self)(other)
        elif isinstance(other, Term):
            return type(self)(self, other)
        else:
            return NotImplemented

    @classmethod
    def truediv_inner(cls, a, b):
        if isinstance(a, cls.convertable_types):
            return cls.truediv_inner(cls(a), b)
        elif isinstance(b, cls.convertable_types):
            return cls.truediv_inner(a, cls(b))
        elif isinstance(a, cls) and isinstance(b, cls):
            return cls(a.coeff/b.coeff, a.powers,
                       imap(lambda (var, power): (var, -power),
                            b.powers.iteritems()))
        else:
            return NotImplemented
    def __truediv__(self, other):
        return self.truediv_inner(self, other)
    def __rtruediv__(self, other):
        return self.truediv_inner(other, self)

    def __div__(self, other):
        return self / other
    def __rdiv__(self, other):
        return other / self

    @classmethod
    def floordiv_inner(cls, a, b):
        if isinstance(a, cls.convertable_types):
            return cls.floordiv_inner(cls(a), b)
        elif isinstance(b, cls.convertable_types):
            return cls.floordiv_inner(a, cls(b))
        elif isinstance(a, cls) and isinstance(b, cls):
            coeff = a.coeff//b.coeff
            powers = dict(a.powers)
            for var, power in b.powers.iteritems():
                powers[var] = powers.get(var, 0) - power
            to_delete = []
            for var, power in powers.iteritems():
                if power <= 0:
                    to_delete.append(var)
            for var in to_delete:
                del powers[var]
            return cls(coeff, powers)
        else:
            return NotImplemented
    def __floordiv__(self, other):
        return self.floordiv_inner(self, other)
    def __rfloordiv__(self, other):
        return self.floordiv_inner(other, self)

    def __radd__(self, other):
        return self + other
    def __add__(self, other):
        if isinstance(other, self.convertable_types):
            return self + type(self)(other)
        elif isinstance(other, Term):
            if self.powers == other.powers:
                return type(self)(self.coeff + other.coeff, self.powers)
            elif self.coeff == 0:
                return type(other)(other.coeff, other.powers)
            elif other.coeff == 0:
                return type(self)(self.coeff, self.powers)
            else:
                raise ArithmeticError("Incompatible terms")
        else:
            return NotImplemented

    def __neg__(self):
        return type(self)(-self.coeff, self.powers)

    def __rsub__(self, other):
        return other + -self
    def __sub__(self, other):
        return self + -other

    def __nonzero__(self):
        return self != 0

    def __hash__(self):
        return hash(self.coeff) ^ hash(self.powers)

    def subsumes(self, other):
        retval = abs(self.coeff) >= abs(other.coeff)
        for var in frozenset(chain(self.powers.iterkeys(), other.powers.iterkeys())):
            retval &= abs(self.powers.get(var, 0)) >= abs(other.powers.get(var, 0))
        return retval

    def compare(self, other, comparison):
        if isinstance(other, self.convertable_types):
            return self == type(self)(other)
        elif isinstance(other, Term):
            retval = comparison(self.coeff, other.coeff)
            for var in frozenset(chain(self.powers.iterkeys(), other.powers.iterkeys())):
                retval &= comparison(self.powers.get(var, 0), other.powers.get(var, 0))
            return retval
        else:
            return NotImplemented
    def __lt__(self, other):
        return self.compare(other, lt)
    def __le__(self, other):
        return self.compare(other, le)
    def __eq__(self, other):
        return self.compare(other, eq)
    def __ne__(self, other):
        return self.compare(other, ne)
    def __gt__(self, other):
        return self.compare(other, gt)
    def __ge__(self, other):
        return self.compare(other, ge)

    def lexicographic_cmp(self, other):
        variables = frozenset(chain(self.powers.iterkeys(), other.powers.iterkeys()))
        for var in sorted(variables):
            c = cmp(self.powers.get(var, 0), other.powers.get(var, 0))
            if c:
                return c
        return 0

    @immutableproperty
    def lexicographic_key(self):
        return cmp_to_key(lambda self, other: self.lexicographic_cmp(other))(self)

    def __str__(self):
        def format_power((var, power)):
            if power == 1:
                return var
            else:
                return "%s**%s" % (var, repr(power))

        if len(self.powers) == 0:
            return repr(self.coeff)
        elif self.coeff == 1:
            return "*".join(imap(format_power, sorted(self.powers.iteritems())))
        else:
            return "%s*%s" % (repr(self.coeff), "*".join(imap(format_power, sorted(self.powers.iteritems()))))

    def __repr__(self):
        return "%s.%s(%s,%s)" % (type(self).__module__,
                                 type(self).__name__,
                                 repr(self.coeff),
                                 dict(self.powers))
    def to_mathematica(self):
        if self.powers:
            return str(self.coeff) + "*" + "*".join(imap(lambda (var, power): var + "^" + str(power), self.powers.iteritems()))
        else:
            return str(self.coeff)
    @classmethod
    def from_mathematica(cls, s):
        coeff, powers = s.split("*")[0], s.split("*")[1:]
        return cls(int(coeff), imap(methodcaller("split", "^"), powers))

    def __copy__(self):
        return type(self)(self.coeff, self.powers)
    def __deepcopy__(self, memo):
        return type(self)(deepcopy(self.coeff, memo), deepcopy(self.powers, memo))

    def __getstate__(self):
        return (self.coeff, self.powers)
    def __setstate__(self, state):
        self.coeff, self.powers = state

    @immutableproperty
    def proper(self):
        return all(imap(lambda x: x > 0, self.powers.itervalues()))

    @immutableproperty
    def vars(self):
        return frozenset(self.powers.iterkeys())
    variables = vars

    @immutableproperty
    def degree(self):
        return sum(self.powers.itervalues())

    @immutableproperty
    def coeff(self):
        raise AttributeError("Uninitialized Term instance")
    @immutableproperty
    def powers(self):
        raise AttributeError("Uninitialized Term instance")


class Polynomial(object):
    __metaclass__ = ImmutableEnforcerMeta
    __slots__ = ['__proper', '__lead_term', '__vars', '__degree', '__terms']
    term_class = Term
    def __init__(self, *args):
        super(Polynomial, self).__init__()
        terms = [self.term_class(0)]

        def put_arg(a):
            if isinstance(a, self.term_class.convertable_types):
                terms.append(self.term_class(a))
            elif isinstance(a, self.term_class):
                terms.append(a)
            elif isinstance(a, Iterable):
                for a in a:
                    put_arg(a)
            else:
                raise TypeError("All arguments to %s.%s must be %s.%s instances" \
                                % (type(self).__module__,
                                   type(self).__name__,
                                   self.term_class.__module__,
                                   self.term_class.__name__))

        for a in args:
            put_arg(a)

        self.terms = self.combine_terms(terms)


    @staticmethod
    def combine_terms(terms):
        new_terms = []
        for t in terms:
            for i in xrange(len(new_terms)):
                try:
                    t += new_terms[i]
                except ArithmeticError:
                    continue
                else:
                    del new_terms[i]
                    break
            new_terms.append(t)
        return(frozenset(new_terms))


    def __pow__(self, other):
        if not isinstance(other, Integral):
            raise TypeError("Can only raise Polynomials to Integral powers")
        sq = self
        accum = type(self)(1)
        for bit in reversed(bin(other)[2:]):
            if bit == "1":
                accum *= sq
            sq *= sq
        return accum

    def __rmul__(self, other):
        return self * other
    def __mul__(self, other):
        if isinstance(other, self.term_class.convertable_types):
            return self * self.term_class(other)
        elif isinstance(other, Term):
            return type(self)(imap(lambda x: x * other, self.terms))
        elif isinstance(other, Polynomial):
            return type(self)(imap(lambda (x, y): x * y, product(self.terms, other.terms)))
        else:
            return NotImplemented

    @classmethod
    def divmod_inner(cls, num, denom):
        assert isinstance(num, cls)
        assert isinstance(denom, cls)

        # This method for polynomial division is taken from section 7.2 of
        # http://www.cs.tamu.edu/academics/tr/tamu-cs-tr-2004-7-4
        # "Designing a Multivariate Polynomial Class: A Starting Point"
        # Brent M. Dingle, Texas A&M University, 2004

        # The algorithm described in the above paper is actually incorrect,
        # it replaces the predicate "If Lead Term of /g/ divides Lead Term of /p/ Then"
        # with the predicate "If Lead Term of /g/ divides /p/ Then"

        P = num
        Q = cls()
        R = cls()
        Zero = cls()
        while P != Zero:
            u = (P.lead_term / denom.lead_term) # true division
            if u.proper:
                U = cls(u)
                Q += U
                P -= ( U * denom )
            else:
                P_l = cls(P.lead_term)
                R += P_l
                P -= P_l
        return (Q, R)

    def __rdivmod__(self,other):
        if isinstance(other, self.term_class.convertable_types):
            return divmod(self.term_class(other), self)
        elif isinstance(other, Term):
            return divmod(type(self)(other), self)
        elif isinstance(other, Polynomial):
            return self.divmod_inner(other, self)
        else:
            return NotImplemented
    def __divmod__(self,other):
        if isinstance(other, self.term_class.convertable_types):
            return divmod(self, self.term_class(other))
        elif isinstance(other, Term):
            return divmod(self, type(self)(other))
        elif isinstance(other, Polynomial):
            return self.divmod_inner(self, other)
        else:
            return NotImplemented

    def __rdiv__(self, other):
        return divmod(other, self)[0]
    def __div__(self, other):
        return divmod(self, other)[0]
    def __rfloordiv__(self, other):
        return divmod(other, self)[0]
    def __floordiv__(self, other):
        return divmod(self, other)[0]

    def __rmod__(self, other):
        return divmod(other, self)[1]
    def __mod__(self, other):
        return divmod(self, other)[1]

    def __radd__(self, other):
        return self + other
    def __add__(self, other):
        if isinstance(other, self.term_class.convertable_types):
            return self + self.term_class(other)
        elif isinstance(other, Term):
            return type(self)(self.terms, other)
        elif isinstance(other, Polynomial):
            return type(self)(self.terms, other.terms)
        else:
            return NotImplemented

    def __neg__(self):
        return type(self)(imap(neg, self.terms))

    def __rsub__(self, other):
        return other + -self
    def __sub__(self, other):
        return self + -other

    def __nonzero__(self):
        return len(self) > 1 or bool(iter(self.terms).next())


    def subsumes(self, other):
        if other == type(other)():
            return True
        if self == type(self)():
            return False
        for i, j in product(self.terms, other.terms):
            if i.subsumes(j)\
                   and type(self)(self.terms - frozenset((i,)))\
                         .subsumes(type(other)(other.terms - frozenset((j,)))):
                return True
        return False

    def __eq__(self, other):
        if isinstance(other, self.term_class.convertable_types):
            return self == self.term_class(other)
        elif isinstance(other, Term):
            return self == type(self)(other)
        elif isinstance(other, Polynomial):
            return self.terms == other.terms
        else:
            return NotImplemented
    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return " + ".join(imap(str, sorted(self.terms, reverse=True,
                                           key=attrgetter('lexicographic_key'))))

    def __repr__(self):
        try:
            return "%s.%s(%s)" % (type(self).__module__,
                                  type(self).__name__,
                                  ", ".join(imap(repr, sorted(self.terms, reverse=True,
                                                              key=attrgetter('lexicographic_key')))))
        except AttributeError:
            return "%s.%s(<uninitialized terms>)" % (type(self).__module__,
                                                     type(self).__name__)
    def to_mathematica(self):
        return "+".join(imap(methodcaller("to_mathematica"), self.terms))
    @classmethod
    def from_mathematica(cls, s):
        s = s.replace(" ", "")
        terms = []
        last_term_end = 0
        for i in xrange(len(s)):
            if s[i] == '-':
                terms.append(cls.term_class.from_mathematica(s[last_term_end:i]))
                last_term_end = i
            if s[i] == '+':
                terms.append(cls.term_class.from_mathematica(s[last_term_end:i]))
                last_term_end = i+1
        return cls(terms)

    def __hash__(self):
        return hash(self.terms)
    def __len__(self):
        return len(self.terms)
    def __iter__(self):
        return iter(self.terms)

    def __copy__(self):
        return type(self)(self.__terms)
    def __deepcopy__(self, memo):
        return type(self)(deepcopy(self.__terms, memo))

    def __getstate__(self):
        return self.terms
    def __setstate__(self, state):
        self.terms = state

    @immutableproperty
    def proper(self):
        return all(imap(attrgetter('proper'), self.terms))

    @immutableproperty
    def lead_term(self):
        return max(self.terms, key=attrgetter('lexicographic_key'))

    @immutableproperty
    def vars(self):
        retval = frozenset()
        for term in self.terms:
            retval |= term.vars
        return retval
    variables = vars

    @immutableproperty
    def degree(self):
        return max(imap(attrgetter('degree'), self.terms))

    @immutableproperty
    def terms(self):
        raise AttributeError("Uninitialized Polynomial instance")


__all__ = ['Term', 'Polynomial']
