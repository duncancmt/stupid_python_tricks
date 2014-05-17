from __future__ import division

from noconflict import classmaker
from immutable import ImmutableEnforcerMeta, ImmutableDict
from itertools import *
from operator import *
from functools import cmp_to_key
from collections import Iterable, Mapping
from numbers import Real

class Term(object):
    __metaclass__ = ImmutableEnforcerMeta
    # TODO: define __slots__
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
            if isinstance(a, Real):
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
        if isinstance(other, Term):
            return type(self)(self.coeff, other.coeff,
                              self.powers, other.powers)
        else:
            return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, Term):
            return type(self)(other.coeff/self.coeff, other.powers,
                              *imap(lambda (var, power): (var, -power),
                                    self.powers.iteritems()))
        else:
            return NotImplemented
    def __truediv__(self, other):
        if isinstance(other, Term):
            return type(self)(self.coeff/other.coeff, self.powers,
                              *imap(lambda (var, power): (var, -power),
                                    other.powers.iteritems()))
        else:
            return NotImplemented
    def __rdiv__(self, other):
        return other / self
    def __div__(self, other):
        return self / other

    def __radd__(self, other):
        return self + other
    def __add__(self, other):
        if isinstance(other, Term):
            if self.powers == other.powers:
                return type(self)(self.coeff + other.coeff, self.powers)
            elif self.coeff == 0:
                return type(other)(other.coeff, other.powers)
            elif other.coeff == 0:
                return type(self)(self.coeff, self.powers)
            else:
                raise ValueError("Incompatible terms")
        else:
            return NotImplemented

    def __neg__(self):
        return type(self)(-self.coeff, self.powers)

    def __rsub__(self, other):
        return other + -self
    def __sub__(self, other):
        return self + -other
    
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
        retval = comparison(self.coeff, other.coeff)
        for var in frozenset(chain(self.powers.iterkeys(), other.powers.iterkeys())):
            retval &= comparison(self.powers.get(var, 0), other.powers.get(var, 0))
        return retval
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
        c = cmp(sum(self.powers.itervalues()), sum(other.powers.itervalues()))
        if c:
            return c
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
        return "Term(%s,%s)" % (repr(self.coeff), dict(self.powers))

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
    def __init__(self, *args):
        terms = [Term(0)]
        for a in args:
            if isinstance(a, Term):
                terms.append(a)
            elif isinstance(a, Iterable):
                for x in a:
                    if not isinstance(x, Term):
                        raise TypeError("All arguments to Polynomial must be Term instances")
                    terms.append(x)
            else:
                raise TypeError("All arguments to Polynomial must be Term instances")
            
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
                except ValueError:
                    pass
            new_terms.append(t)
        return(frozenset(new_terms))
        

    def __rmul__(self, other):
        return self * other
    def __mul__(self, other):
        if isinstance(other, Term):
            return type(self)(imap(lambda x: x * other, self.terms))
        elif isinstance(other, Polynomial):
            return type(self)(imap(lambda (x, y): x * y, product(self.terms, other.terms)))
        else:
            return NotImplemented

    def __divmod__(self,other):
        if isinstance(other, Term):
            return (type(self)(imap(lambda x: x/other, self.terms)), type(self)(Term(0)))
        elif not isinstance(other, Polynomial):
            return NotImplemented

        # This method for polynomial division is taken from section 7.2 of
        # http://www.cs.tamu.edu/academics/tr/tamu-cs-tr-2004-7-4
        # "Designing a Multivariate Polynomial Class: A Starting Point"
        # Brent M. Dingle, Texas A&M University, 2004

        # The algorithm described in the above paper is actually incorrect,
        # it replaces the predicate "If Lead Term of /g/ divides Lead Term of /p/ Then"
        # with the predicate "If Lead Term of /g/ divides /p/ Then"

        P = self
        Q = Polynomial(Term(0))
        R = Polynomial(Term(0))
        Zero = Polynomial(Term(0))
        while P != Zero:
            u = (P.lead_term / other.lead_term)
            if u.proper:
                U = Polynomial(u)
                Q += U
                P -= ( U * other )
            else:
                P_l = Polynomial(P.lead_term)
                R += P_l
                P -= P_l
        return (Q, R)
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
        if isinstance(other, Term):
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

    @property
    def proper(self):
        return all(imap(attrgetter('proper'), self.terms))

    def __eq__(self, other):
        return self.terms == other.terms

    def __str__(self):
        return " + ".join(imap(str, sorted(self.terms, reverse=True,
                                           key=attrgetter('lexicographic_key'))))

    def __repr__(self):
        return "Polynomial(%s)" % ", ".join(imap(repr, sorted(self.terms, reverse=True,
                                                              key=attrgetter('lexicographic_key'))))

    def __hash__(self):
        return hash(self.terms)
    def __len__(self):
        return len(self.terms)
    def __iter__(self):
        return iter(self.terms)

    @property
    def lead_term(self):
        max(self.terms, key=attrgetter('lexicographic_key'))

    @property
    def terms(self):
        return self.__terms
    @terms.setter
    def terms(self, value):
        self.__terms = value


def horner_form(thing, var=None):
    if not thing.proper:
        raise ValueError('Can only put proper Terms and Polynomials into horner form')
    if isinstance(thing, Term):
        term = thing
        del thing
        if len(term.powers) == 0:
            return [(term, var)]
        else:
            if term.coeff != 1:
                ops = [(Term(term.coeff), var)]
            else:
                ops = []
            for var, power in term.powers.iteritems():
                for _ in xrange(power):
                    ops.append((Term(0), var))
            return ops
    elif var is None:
        if not isinstance(thing, Polynomial):
            # immediate error
            horner_form(thing, object())
        poly = thing
        del thing
        vars = set()
        for term in poly:
            for var in term.powers.iterkeys():
                vars.add(var)
        def count_ops(ops):
            if isinstance(ops, Term):
                return 1
            else:
                retval = 0
                for op, var in ops:
                    retval += count_ops(op)
                return retval

        if len(vars) == 0:
            assert len(poly) == 1
            term = iter(poly).next()
            return horner_form(term, var=None)
        else:
            return max(imap(lambda var: horner_form(poly, var), vars),
                       key=count_ops)
    elif isinstance(thing, Polynomial):
        poly = thing
        del thing
        if len(poly) == 0:
            return horner_form(Term(0), var)
        if len(poly) == 1:
            term = iter(poly).next()
            return horner_form(term, var)
        else:
            max_power = max(imap(lambda term: term.powers.get(var, 0), poly.terms))
            coeffs = [Polynomial(Term(0))]*(max_power+1)
            for term in poly:
                power = term.powers.get(var, 0)
                coeffs[power] += term / Term((var, power))
            ops = [ (horner_form(coeff, var=None), var) for coeff in reversed(coeffs) ]
            return ops
    else:
        raise TypeError("Unknown type %s in horner_form" % repr(type(thing)), thing)

def horner_clean(form):
    if isinstance(form, Iterable):
        result = []
        for op, var in form:
            result.append((horner_clean(op), var))
        return tuple(result)
    elif isinstance(form, Term):
        assert len(form.powers) == 0
        return form.coeff
    else:
        return form

def horner_evaluate(form, values):
    result = 0
    for op, var in form:
        if isinstance(op, Iterable):
            coeff = horner_evaluate(op, values)
        elif isinstance(op, Term):
            assert len(op.powers) == 0
            coeff = op.coeff
        else:
            coeff = op

        if var is None:
            assert result == 0
        else:
            result *= values[var]
        result += coeff
    return result

__all__ = ['Term', 'Polynomial', 'horner_form', 'horner_clean', 'horner_evaluate']
