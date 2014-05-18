from __future__ import division

from polynomial import *
from collections import Iterable
from itertools import imap

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
            coeffs = [Polynomial()]*(max_power+1)
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

__all__ = ['horner_form', 'horner_clean', 'horner_evaluate']
