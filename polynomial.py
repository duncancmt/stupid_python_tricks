from itertools import *
from operator import *
from collections import Iterable
from numbers import Real

# TODO: make shit immutable

class Term(object):
    def __init__(self, *args):
        super(Term, self).__init__()
        self.coeff = 1
        self.powers = dict()

        def put_var(var, power):
            if not isinstance(var, basestring):
                raise TypeError("Invalid variable name",var)
            if not isinstance(power, Real):
                raise TypeError("Invalid variable power",power)
            self.powers[var] = self.powers.get(var, 0) + power


        for a in args:
            if isinstance(a, Real):
                self.coeff *= a
            elif isinstance(a, basestring):
                self.powers[a] = self.powers.get(a, 0) + 1
            elif isinstance(a, dict):
                for (var, power) in a.iteritems():
                    put_var(var, power)
            elif isinstance(a, tuple):
                put_var(*a)
            else:
                raise TypeError("Invalid term element",a)
        self.trim_powers()

    def trim_powers(self):
        to_delete = []
        for var, power in self.powers.iteritems():
            if power == 0:
                to_delete.append(var)
        for var in to_delete:
            del self.powers[var]

    def __rmul__(self, other):
        return self * other
    def __mul__(self, other):
        return type(self)(self.coeff, other.coeff,
                          self.powers, other.powers)

    def __radd__(self, other):
        return self + other
    def __add__(self, other):
        if self.powers == other.powers:
            return type(self)(self.coeff + other.coeff, self.powers)
        else:
            raise ValueError("Incompatible terms")

    def __neg__(self):
        return type(self)(-self.coeff, self.powers)

    def __rsub__(self, other):
        return other + -self
    def __sub__(self, other):
        return self + -other
    
    def __hash__(self):
        return hash(frozenset((self.coeff,))|frozenset(self.powers.iteritems()))


    def compare(self, other, comparison):
        retval = comparison(self.coeff, other.coeff)
        for var, power in self.powers.iteritems():
            retval &= comparison(self.powers[var], self.other.powers.get(var, 0))
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

    def __repr__(self):
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

class Polynomial(object):
    def __init__(self, *args):
        terms = []
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
            
        self.terms = frozenset(terms)
        self.combine_terms()

    def combine_terms(self):
        new_terms = []
        for t in self.terms:
            for i in xrange(len(new_terms)):
                try:
                    t += new_terms[i]
                    del new_terms[i]
                    break
                except ValueError:
                    pass
            new_terms.append(t)
        self.terms = frozenset(new_terms)
        

    def __rmul__(self, other):
        return self * other
    def __mul__(self, other):
        return type(self)(imap(lambda (x, y): x * y, product(self.terms, other.terms)))

    def __radd__(self, other):
        return self + other
    def __add__(self, other):
        return type(self)(self.terms, other.terms)

    def __neg__(self):
        return type(self)(imap(neg, self.terms))

    def __rsub__(self, other):
        return other + -self
    def __sub__(self, other):
        return self + -other


    def compare(self, other, comparison):
        for i, j in product(self.terms, other.terms):
            if comparison(i, j):
                if type(self)(self.terms - frozenset((i,)))\
                       .compare(type(other)(other.terms - frozenset((j,))),
                                comparison):
                    return True
        return False
    def __lt__(self, other):
        return self.compare(other, lt)
    def __le__(self, other):
        return self.compare(other, le)
    def __eq__(self, other):
        return self.terms == other.terms
    def __ne__(self, other):
        return self.terms != other.terms
    def __gt__(self, other):
        return self.compare(other, gt)
    def __ge__(self, other):
        return self.compare(other, ge)

    def __repr__(self):
        return " + ".join(imap(repr, sorted(self.terms, reverse=True,
                                            cmp=lambda x,y: x.lexicographic_cmp(y))))
