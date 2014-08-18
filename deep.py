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


from itertools import izip, count, imap
from collections import Sequence, Iterable, Callable

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


def shape(tensor):
    if isinstance(tensor, Sequence):
        shapes = map(shape, tensor)
        assert all(imap(lambda s: s == shapes[0], shapes[1:]))
        return (len(shapes),)+shapes[0]
    else:
        return ()


def tensor_from_shape(s, fill=None):
    if len(s) == 0:
        if isinstance(fill, Callable):
            return fill()
        else:
            return fill
    else:
        retval = [ tensor_from_shape(s[1:], fill=fill) for _ in xrange(s[0]) ]
        assert shape(retval) == tuple(s)
        return retval


__all__ = ['deep_foreach', 'deep_map', 'deep_setitem', 'deep_getitem', 'deep_flatten', 'shape', 'tensor_from_shape']
