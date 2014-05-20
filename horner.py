from __future__ import division

from polynomial import *
from collections import Iterable
from itertools import imap
from numbers import Real

def _horner_form_term(term, var, recurse):
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

def _horner_form_search(poly, recurse):
    if len(poly.vars) == 0:
        assert len(poly) == 1
        term = iter(poly).next()
        return recurse(term, None)
    else:
        return max(imap(lambda var: recurse(poly, var), poly.vars),
                   key=horner_count_ops)

def _horner_form_poly(poly, var, recurse):
    if len(poly) == 0:
        return recurse(Term(0), var)
    if len(poly) == 1:
        term = iter(poly).next()
        return recurse(term, var)
    else:
        max_power = max(imap(lambda term: term.powers.get(var, 0), poly.terms))
        coeffs = [Polynomial()]*(max_power+1)
        for term in poly:
            power = term.powers.get(var, 0)
            coeffs[power] += term / Term((var, power))
        ops = [ (recurse(coeff, None), var) for coeff in reversed(coeffs) ]
        return ops

def _horner_cleanup(form):
    if isinstance(form, Iterable):
        result = []
        for op, var in form:
            result.append((_horner_cleanup(op), var))
        return tuple(result)
    elif isinstance(form, Term):
        assert len(form.powers) == 0
        return form.coeff
    else:
        return form


def horner_form(thing):
    """Return the sequence of Horner's method operations that evaluates the argument
    performs search on variables to determine the optimal order to evaluate them
    is otherwise a greedy algorithm"""
    def inner(thing, var):
        if not thing.proper:
            raise ValueError('Can only put proper Terms and Polynomials into horner form')
        if isinstance(thing, Term):
            return _horner_form_term(thing, var, inner)
        elif var is None:
            if not isinstance(thing, Polynomial):
                # immediate error
                inner(thing, object())
            return _horner_form_search(thing, inner)
        elif isinstance(thing, Polynomial):
            return _horner_form_poly(thing, var, inner)
        else:
            raise TypeError("Unknown type %s in horner_form" % repr(type(thing)), thing)

    return _horner_cleanup(inner(thing, None))


def horner_count_ops(ops):
    if isinstance(ops, Iterable):
        retval = 0
        for op, var in ops:
            retval += horner_count_ops(op)
        return retval
    else:
        return 1


def horner_evaluate(ops, values):
    result = 0
    for op, var in ops:
        if isinstance(op, Iterable):
            coeff = horner_evaluate(op, values)
        else:
            coeff = op

        if var is None:
            assert result == 0
        else:
            result *= values[var]
        result += coeff
    return result

__all__ = ['horner_form', 'horner_count_ops', 'horner_evaluate']
