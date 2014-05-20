from __future__ import division

from noconflict import classmaker
from immutable import ImmutableEnforcerMeta, ImmutableDict
from itertools import *
from operator import *
from functools import cmp_to_key
from collections import Iterable, Mapping
from numbers import Real
from copy import copy,deepcopy

class Term(object):
    __metaclass__ = ImmutableEnforcerMeta
    # TODO: define __slots__
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

    def __rmul__(self, other):
        return self * other
    def __mul__(self, other):
        if isinstance(other, self.convertable_types):
            return self * type(self)(other)
        elif isinstance(other, Term):
            return type(self)(self, other)
        else:
            return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, self.convertable_types):
            return type(self)(other) / self
        elif isinstance(other, Term):
            return type(self)(other.coeff/self.coeff, other.powers,
                              imap(lambda (var, power): (var, -power),
                                   self.powers.iteritems()))
        else:
            return NotImplemented
    def __truediv__(self, other):
        if isinstance(other, self.convertable_types):
            return self / type(self)(other)
        elif isinstance(other, Term):
            return type(self)(self.coeff/other.coeff, self.powers,
                              imap(lambda (var, power): (var, -power),
                                   other.powers.iteritems()))
        else:
            return NotImplemented
    def __rdiv__(self, other):
        return other / self
    def __div__(self, other):
        return self / other

    def __rfloordiv__(self, other):
        if isinstance(other, self.convertable_types):
            return type(self)(other) // self
        elif isinstance(other, Term):
            coeff = other.coeff // self.coeff
            powers = dict(other.powers)
            for var, power in self.powers.iteritems():
                powers[var] = powers.get(var, 0) - power
            to_delete = []
            for var, power in powers.iteritems():
                if power <= 0:
                    to_delete.append(var)
            for var in to_delete:
                del powers[var]
            return type(self)(coeff, powers)
        else:
            return NotImplemented
    def __floordiv__(self, other):
        if isinstance(other, self.convertable_types):
            return self // type(self)(other)
        elif isinstance(other, Term):
            coeff = self.coeff//other.coeff
            powers = dict(self.powers)
            for var, power in other.powers.iteritems():
                powers[var] = powers.get(var, 0) - power
            to_delete = []
            for var, power in powers.iteritems():
                if power <= 0:
                    to_delete.append(var)
            for var in to_delete:
                del powers[var]
            return type(self)(coeff, powers)
        else:
            return NotImplemented

    def __rdivmod__(self, other):
        if isinstance(other, self.convertable_types):
            return divmod(type(self)(other), self)
        elif isinstance(other, Term):
            q_coeff, r_coeff = divmod(other.coeff, self.coeff)
            powers = dict(other.powers)
            for var, power in self.powers.iteritems():
                powers[var] = powers.get(var, 0) - power
            q_powers = dict()
            r_powers = dict()
            for var, power in powers.iteritems():
                if power < 0:
                    r_powers[var] = -power
                elif power > 0:
                    q_powers[var] = power
            return (type(self)(q_coeff, q_powers),
                    type(self)(r_coeff, r_powers))
        else:
            return NotImplemented
    def __divmod__(self, other):
        if isinstance(other, self.convertable_types):
            return divmod(self, type(self)(other))
        elif isinstance(other, Term):
            q_coeff, r_coeff = divmod(self.coeff, other.coeff)
            powers = dict(self.powers)
            for var, power in other.powers.iteritems():
                powers[var] = powers.get(var, 0) - power
            q_powers = dict()
            r_powers = dict()
            for var, power in powers.iteritems():
                if power < 0:
                    r_powers[var] = -power
                elif power > 0:
                    q_powers[var] = power
            return (type(self)(q_coeff, q_powers),
                    type(self)(r_coeff, r_powers))
        else:
            return NotImplemented

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

    @property
    def proper(self):
        return all(imap(lambda x: x > 0, self.powers.itervalues()))

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

    lexicographic_key = property(cmp_to_key(lexicographic_cmp))

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

    def __copy__(self):
        return type(self)(self.coeff, self.powers)
    def __deepcopy__(self, memo):
        return type(self)(deepcopy(self.coeff, memo), deepcopy(self.powers, memo))

    def __getstate__(self):
        return (self.coeff, self.powers)
    def __setstate__(self, state):
        self.coeff, self.powers = state

    @property
    def vars(self):
        try:
            return self.__vars
        except AttributeError:
            self.vars = frozenset(self.powers.iterkeys())
            return self.vars
    @vars.setter
    def vars(self, value):
        self.__vars = value
    @property
    def variables(self):
        return self.vars

    @property
    def degree(self):
        return sum(self.powers.itervalues())

    @property
    def coeff(self):
        return self.__coeff
    @coeff.setter
    def coeff(self, value):
        self.__coeff = value
    @property
    def powers(self):
        return self.__powers
    @powers.setter
    def powers(self, value):
        self.__powers = value

class PolynomialBase(object):
    __metaclass__ = ImmutableEnforcerMeta
class Polynomial(PolynomialBase, Iterable):
    __metaclass__ = classmaker()

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
                    del new_terms[i]
                    break
                except ArithmeticError:
                    pass
            new_terms.append(t)
        return(frozenset(new_terms))
        

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
        assert isinstance(dneom, cls)

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
            return (type(self)(imap(lambda x: other/x, self.terms)), type(self)(self.term_class(0)))
        elif not isinstance(other, Polynomial):
            return self.divmod_inner(other, self)
        else:
            return NotImplemented
    def __divmod__(self,other):
        if isinstance(other, self.term_class.convertable_types):
            return divmod(self, self.term_class(other))
        elif isinstance(other, Term):
            return (type(self)(imap(lambda x: x/other, self.terms)), type(self)(self.term_class(0)))
        elif not isinstance(other, Polynomial):
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

    def __str__(self):
        return " + ".join(imap(str, sorted(self.terms, reverse=True,
                                           key=attrgetter('lexicographic_key'))))

    def __repr__(self):
        return "%s.%s(%s)" % (type(self).__module__,
                              type(self).__name__,
                              ", ".join(imap(repr, sorted(self.terms, reverse=True,
                                                          key=attrgetter('lexicographic_key')))))

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

    @property
    def proper(self):
        try:
            return self.__proper
        except AttributeError:
            self.proper = all(imap(attrgetter('proper'), self.terms))
            return self.proper
    @proper.setter
    def proper(self, value):
        self.__proper = value

    @property
    def lead_term(self):
        try:
            return self.__lead_term
        except AttributeError:
            self.lead_term = max(self.terms, key=attrgetter('lexicographic_key'))
            return self.lead_term
    @lead_term.setter
    def lead_term(self, value):
        self.__lead_term = value

    @property
    def vars(self):
        try:
            return self.__vars
        except AttributeError:
            retval = frozenset()
            for term in self.terms:
                retval |= term.vars
            self.vars = retval
            return self.vars
    @vars.setter
    def vars(self, value):
        self.__vars = value
    @property
    def variables(self):
        return self.vars

    @property
    def degree(self):
        return max(imap(methodcaller('degree'), self.terms))

    @property
    def terms(self):
        return self.__terms
    @terms.setter
    def terms(self, value):
        self.__terms = value


__all__ = ['Term', 'Polynomial']
