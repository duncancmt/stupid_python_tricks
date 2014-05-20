from __future__ import division

from polynomial import *
from collections import Iterable
from itertools import imap, izip, ifilter, chain, combinations, product
from operator import mul
from numbers import Real

from memoize import memoize

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
        return min(imap(lambda var: recurse(poly, var), poly.vars),
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

@memoize
def horner_form_basic(thing):
    """Return the sequence of Horner's method operations that evaluates the argument
    chooses variables in lexicographic order and is a purely greedy algorithm."""
    if not thing.proper:
        raise ValueError('Can only put proper Terms and Polynomials into Horner form')
    def inner(thing, _):
        var = min(thing.vars) if thing.vars else None
        if isinstance(thing, Term):
            return _horner_form_term(thing, var, inner)
        elif isinstance(thing, Polynomial):
            return _horner_form_poly(thing, var, inner)
        else:
            raise TypeError("Unknown type %s in horner_form_basic" % repr(type(thing)), thing)
    return _horner_cleanup(inner(thing, None))

def horner_form(thing):
    """Return the sequence of Horner's method operations that evaluates the argument
    performs search on variables to determine the optimal order to evaluate them
    is otherwise a greedy algorithm"""
    if not thing.proper:
        raise ValueError('Can only put proper Terms and Polynomials into Horner form')

    @memoize
    def inner(thing, var):
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


def egcd(a, b):
    """The Extended Euclidean Algorithm
    In addition to finding the greatest common divisor (GCD) of the
    arguments, also find and return the coefficients of the linear
    combination that results in the GCD.
    """
    if a == 0:
        return (b, 0, 1)
    else:
        quot, rem = divmod(b, a)
        g, y, x = egcd(rem, a)
        return (g, x - quot * y, y)

def gcd(a, b):
    return egcd(a, b)[0]

def horner_form_tmp(poly, n_tmps=None, monitor=lambda *args: None):
    if not isinstance(poly, Polynomial):
        raise TypeError("Can only put Polynomial instances into Horner form with temporary storage")

    for var in poly.vars:
        if var.startswith("tmp"):
            raise ValueError('Variables beginning with "tmp" are reserved for use by horner_form_tmp')

    if n_tmps is None:
        n_tmps = len(poly)

    def get_common(subset):
        def inner(a, b):
            retval = gcd(a, b)
            if retval.degree < 2:
                raise ArithmeticError
            else:
                return retval
        try:
            return reduce(inner, subset)
        except ArithmeticError:
            return None


    possible_tmps = set()
    for common in ifilter(lambda x: x is not None,
                          imap(get_common,
                               chain.from_iterable(imap(lambda i: combinations(poly, i),
                                                        xrange(2, len(poly)+1))))):
        if common.degree < 2:
            continue
        monitor("common", common)
        possible_tmps.add(common)

    def make_tmp():
        retval = "tmp"+str(make_tmp.counter)
        make_tmp.counter += 1
        return retval
    make_tmp.counter = 0

    def zip_tmps(x):
        zipped0 = zip(*x)
        zipped1 = zip(*zipped0[1])
        return (zipped0[0], zipped1)

    best = (None, None)
    for names, (tmps, tmps_ops) in imap(zip_tmps,
                                        combinations(imap(lambda tmps: (make_tmp(), (tmps, horner_form(tmps))),
                                                          possible_tmps), n_tmps)):
        monitor("get_possible_terms", tmps)
        possible_terms = set()
        for term in poly.terms:
            monitor("get_term_alternatives", term)
            possibilities = {term}
            for names_, tmps_ in imap(lambda x: zip(*x),
                                      chain.from_iterable(imap(lambda i: combinations(izip(names, tmps), i),
                                                               xrange(1, len(names)+1)))):
                common = reduce(mul, tmps_)
                quot, rem = divmod(term, common)
                if rem == 0:
                    quot = reduce(mul, names_, quot)
                    monitor("alternative", quot)
                    if not any(imap(lambda x: quot.vars - poly.vars <= x.vars - poly.vars, possibilities)):
                        to_delete = []
                        for possibility in possibilities:
                            if possibility.vars - poly.vars <= quot.vars - poly.vars:
                                to_delete.append(possibility)
                        for possibility in to_delete:
                            possibilities.remove(possibility)
                        possibilities.add(quot)
            monitor("all_term_alternatives", possibilities)
            possible_terms.add(frozenset(possibilities))
        monitor("all_possible_terms", possible_terms)

        tmps_best = (None, None)
        for terms in product(*possible_terms):
            ops = horner_form(Polynomial(*terms))
            count_ops = horner_count_ops(ops)
            monitor("evaluate_term_alternatives", terms, count_ops, tmps_best[0])
            if tmps_best[0] is None or count_ops < tmps_best[0]:
                tmps_best = (count_ops, ops)

        total_count_ops = tmps_best[0] + sum(imap(horner_count_ops, tmps_ops))
        monitor("evaluate_tmp_alternatives", tmps, total_count_ops, best[0])
        # NOTE: doesn't take into consideration that one tmp may be derivable from another
        if best[0] is None or total_count_ops < best[0]:
            best_dict = {None:tmps_best[0]}
            best_dict.update(izip(names, tmps_ops))
            best = (total_count_ops, best_dict)
    return best[1]

__all__ = ['horner_form_basic', 'horner_form', 'horner_form_tmp', 'horner_count_ops', 'horner_evaluate']
