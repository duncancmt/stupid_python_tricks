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


from itertools import *

def flatten(lol):
    """Flattens one level of nesting of the given iterator"""
    return chain.from_iterable(lol)

def heads(l, include_empty=True):
    """Yields each subsequence of the argument that begins with the first element of the argument."""
    ret = []
    if include_empty:
        yield ()
    for i in l:
        ret.append(i)
        yield tuple(ret)

def partitions(s):
    """Consider the argument as a set of elements. Yield all partitions of that set in order of decreasing fineness."""
    try:
        this = s.next()
    except AttributeError:
        for partition in partitions(iter(s)):
            yield partition
    else:
        bottom_level = True
        for partition in partitions(s):
            bottom_level = False
            yield ((this,),) + partition
            for i in xrange(len(partition)):
                yield partition[:i] + ((this,) + partition[i],) + partition[i+1:]
        if bottom_level:
            yield ((this,),)
        raise StopIteration

def count_iterator(i):
    """Counts the number of elements in the argument."""
    ret = 0
    for _ in i:
        ret += 1
    return ret


__all__ = ['flatten', 'heads', 'partitions', 'count_iterator']
