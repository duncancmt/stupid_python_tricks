from itertools import izip, count
from collections import Sequence, Iterable

def deep_foreach(f, l, i=()):
    """Applies f to each atomic element of l and the index of that element"""
    if isinstance(l, Sequence):
        for j in xrange(len(l)):
            deep_foreach(f, l[j], i+(j,))
    else:
        f(l,i)

def deep_map(f, l, i=()):
    """Applies f to each atomic element of l and the index of that element.
    return the result of those applications in the same shape as l"""
    if isinstance(l, Sequence):
        return [ deep_map(f, l[j], i+(j,)) for j in xrange(len(l)) ]
    else:
        return f(l,i)

def deep_setitem(s, i, x):
    """sets the i element of s to x where i is a tuple of indexes"""
    if len(i) == 1:
        s[i[0]] = x
    else:
        deep_setitem(s[i[0]], i[1:], x)

def deep_getitem(s, i):
    """get the i element of s where i is a tuple of indexes"""
    if len(i) == 1:
        return s[i[0]]
    else:
        return deep_getitem(s[i[0]], i[1:])

def deep_flatten(l, enumerate=False):
    """Yield the atomic elements contained in l.
    If enumerate is true, yield a tuple of (atomic element, indexes) where indexes is itself a tuple."""
    schedule = [(l,())]
    while len(schedule) > 0:
        (x, index) = schedule.pop()
        if isinstance(x, Iterable):
            # TODO: don't use reversed to avoid consing a new list
            for (next, i) in reversed(list(izip(x,count()))):
                schedule.append((next, index+(i,)))
        else:
            if enumerate:
                yield (x, index)
            else:
                yield x
    raise StopIteration

__all__ = ['deep_foreach', 'deep_map', 'deep_setitem', 'deep_getitem', 'deep_flatten']
