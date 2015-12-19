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

# this module mostly taken from https://code.activestate.com/recipes/576930/

from random import random, getrandbits
from math import log
from collections import namedtuple

# TODO: threadsafety



SkipListElem = namedtuple('SkipListElem', ('value', 'next', 'span'))



class SkipList(object):
    def __init__(self, iterable=()):
        height = 1
        sentinel = object()
        self.height = height
        self.sentinel = sentinel
        self.head = SkipListElem(sentinel, [sentinel]*height, [1]*height)
        self.size = 0
        for elem in iterable:
            self.add(elem)


    def walk(self, pred):
        height = self.height
        sentinel = self.sentinel

        chain = [sentinel] * height
        steps = [0] * height
        node = self.head
        for level in xrange(height-1, -1, -1):
            while node.next[level] is not sentinel \
                  and pred(sum(steps) + node.span[level],
                           node.next[level].value):
                steps[level] += node.span[level]
                node = node.next[level]
            chain[level] = node
        return (chain, steps)


    def add(self, value):
        height = self.height
        sentinel = self.sentinel
        head = self.head

        new_height = min(height, 1 - int(log(random(), 2.)))
        new = SkipListElem(value, [None]*new_height, [None]*new_height)
        chain, steps = self.walk(lambda i, x: x <= value)
        i = 0
        for level in xrange(new_height):
            prev = chain[level]
            new.next[level] = prev.next[level]
            prev.next[level] = new
            new.span[level] = prev.span[level] - i
            prev.span[level] = i
            i += steps[level]
        for level in xrange(height):
            chain[level].span[level] += 1

        self.size += 1
        if self.size > 2**(height + 1):
            MAY, MUST, MUST_NOT = object(), object(), object()
            promote = MUST
            node = self.head
            node.next.append(sentinel)
            node.span.append(node.span[height-1])
            prev = node
            node = node.next[height-1]
            while node is not sentinel:
                if promote is MAY:
                    if getrandbits(1):
                        node.next.append(sentinel)
                        node.span.append(node.span[height-1])
                        prev.next[height] = node
                        prev = node
                        promote = MUST_NOT
                    else:
                        prev.span[height] += node.span[height-1]
                        promote = MUST
                elif promote is MUST:
                    node.next.append(sentinel)
                    node.span.append(node.span[height-1])
                    prev.next[height] = node
                    prev = node
                    promote = MAY
                else: # promote is MUST_NOT
                    prev.span[height] += node.span[height-1]
                    promote = MAY
                node = node.next[height-1]
            self.height += 1


    def remove(self, value):
        height = self.height
        sentinel = self.sentinel

        chain, steps = self.walk(lambda i, x: x < value)
        old = chain[0].next[0]
        if old is sentinel or chain[0].next[0].value != value:
            raise ValueError("%s is not in %s" % (value, type(self).__name__))
        for level in xrange(len(chain[0].next[0].next)):
            prev = chain[level]
            prev.next[level] = old.next[level]
            prev.span[level] += old.span[level]
        for level in xrange(height):
            chain[level].span[level] -= 1

        self.size -= 1
        if self.size < (1 << height) and height > 1:
            node = self.head
            while node is not sentinel:
                node.span.pop()
                node = node.next.pop()
            self.height -= 1


    def index(self, value):
        chain, steps = self.walk(lambda i, x: x <= value)
        if chain[0].value != value:
            raise ValueError("%s i snot in %s" % (value, type(self).__name__))
        return sum(steps)-1


    def __getitem__(self, index):
        if index < -len(self):
            raise IndexError("%s index out of range" % type(self).__name__)
        elif index < 0:
            index += len(self)
        index += 1
        chain, steps = self.walk(lambda i, x: i <= index)
        sentinel = self.sentinel
        if chain[0] is sentinel:
            raise IndexError("%s index out of range" % type(self).__name__)
        return chain[0].value


    def __delitem__(self, index):
        if index < -len(self):
            raise IndexError("%s index out of range" % type(self).__name__)
        elif index < 0:
            index += len(self)

        height = self.height
        sentinel = self.sentinel

        chain, steps = self.walk(lambda i, x: i <= index)
        if chain[0].next[0] is sentinel:
            raise IndexError("%s deletion index out of ragne" % type(self).__name__)
        old = chain[0].next[0]
        for level in xrange(len(old.next)):
            prev = chain[level]
            prev.next[level] = old.next[level]
            prev.span[level] += old.span[level]
        for level in xrange(height):
            chain[level].span[level] -= 1

        self.size -= 1
        if self.size < (1 << height) and height > 1:
            node = self.head
            while node is not sentinel:
                node.span.pop()
                node = node.next.pop()
            self.height -= 1


    def __len__(self):
        return self.size


    def __iter__(self):
        sentinel = self.sentinel
        node = self.head.next[0]
        while node is not sentinel:
            yield node.value
            node = node.next[0]


    def preen(self):
        height = self.height
        sentinel = self.sentinel
        head = self.head

        MAY, MUST, MUST_NOT = object(), object(), object()
        promote = [None] + [MUST] * (height-1)
        steps   = [None] + [0]    * (height-1)
        chain   = [None] + [head] * (height-1)
        node = head.next[0]
        while node is not sentinel:
            for level in xrange(1, height):
                steps[level] += 1
            for level in xrange(1, height):
                if promote[level] is MAY:
                    if getrandbits(1):
                        prev = chain[level]
                        prev.next[level:] = (node,)
                        prev.span[level:] = (steps[level],)
                        chain[level] = node
                        steps[level] = 0
                        promote[level] = MUST_NOT
                    else:
                        promote[level] = MUST
                        del node.next[level:]
                        del node.span[level:]
                        break
                elif promote[level] is MUST:
                    prev = chain[level]
                    prev.next[level:] = (node,)
                    chain[level] = node
                    prev.span[level:] = (steps[level],)
                    steps[level] = 0
                    promote[level] = MAY
                else: # promote[level] is MUST_NOT
                    promote[level] = MAY
                    del node.next[level:]
                    del node.span[level:]
                    break
            node = node.next[0]
        for level in xrange(1, height):
            prev = chain[level]
            prev.next[level:] = (sentinel,)
            prev.span[level:] = (steps[level]+1,)


    @property
    def heights(self):
        sentinel = self.sentinel
        node = self.head.next[0]
        while node is not sentinel:
            yield len(node.next)
            node = node.next[0]


__all__ = [ 'SkipList' ]



if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print "Usage: %s test_size" % sys.argv[0]

    from random import randrange, sample, shuffle
    from math import ceil
    from bisect import bisect_left
    test_size = int(sys.argv[1])

    def check_SkipList(sl, l):
        print >>sys.stderr, "checking"
        r = range(len(sl))
        assert sorted(sl) == l
        assert [ sl[i] for i in r ] == l
        assert all(sl[sl.index(v)] == v for v in sl)
        print >>sys.stderr, "preening"
        sl.preen()
        print >>sys.stderr, "checking"
        assert sorted(sl) == l
        assert [ sl[i] for i in r ] == l
        assert all(sl[sl.index(v)] == v for v in sl)


    print >>sys.stderr, "Creating a SkipList with %d random elements" % test_size
    a = SkipList( randrange(test_size*2) for _ in xrange(test_size) )
    b = list(a)
    check_SkipList(a, b)

    while a:
        delete_count = int(ceil(len(a) / 2.))
        print >>sys.stderr, "Deleting %d indexes (%d remain)" % (delete_count, len(a) - delete_count)
        for _ in xrange(delete_count):
            i = randrange(len(a))
            del a[i]
            del b[i]
        check_SkipList(a, b)

    print >>sys.stderr, "Creating a SkipList with %d random elements" % test_size
    a = SkipList( randrange(test_size*2) for _ in xrange(test_size) )
    b = list(a)
    check_SkipList(a, b)

    while a:
        delete_count = int(ceil(len(a) / 2.))
        print >>sys.stderr, "Deleting %d elements (%d remain)" % (delete_count, len(a) - delete_count)
        population = sample(a, delete_count)
        shuffle(population)
        for elem in population:
            a.remove(elem)
            del b[bisect_left(b, elem)]
        check_SkipList(a, b)

    print >>sys.stderr, "Tests passed!"
