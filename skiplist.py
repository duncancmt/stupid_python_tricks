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

from random import getrandbits
from math import log

# TODO: threadsafety
# TODO: count, extend
# TODO: __add__, __radd__, __iadd__, __mul__, __rmul__, __imul__
# TODO: __contains__


class SkipList(object):
    def __init__(self, iterable=()):
        self.height = 1
        self.sentinel = object()

        # value, prev, next[0], span[0], next[1], span[1]...
        self.head = [object(), self.sentinel, self.sentinel, 1]

        self.tail = self.head
        self.size = 0
        for elem in iterable:
            self.add(elem)


    def add(self, value):
        """Insert the argument `value` into the SkipList.
    The insertion position of `value` is *after* any existing elements
    that compare equal to `value`; this preserves insertion order when
    iterating and means that `iter(SkipList(iterable))` is a stable
    sort over `iterable`.
"""

        height = self.height
        sentinel = self.sentinel
        head = self.head

        chain = [None] * (2 + 2*height)
        node = self.head
        for level in xrange(2*height, 0, -2):
            chain[level + 1] = 0
            while node[level] is not sentinel \
                  and node[level][0] <= value:
                chain[level + 1] += node[level + 1]
                node = node[level]
            chain[level] = node

        sample = 1 << height
        while sample == 1 << height:
            sample = getrandbits(height) + 1
        new_height = int(log(sample, 2.)) + 1
        new = [value, chain[2]] + [None, None]*new_height
        i = 0
        for level in xrange(2, 2 + 2*new_height, 2):
            prev = chain[level]
            new[level] = prev[level]
            prev[level] = new
            new[level + 1] = prev[level + 1] - i
            prev[level + 1] = i
            i += chain[level + 1]
        if new[2] is sentinel:
            self.tail = new
        else:
            new[2][1] = new
        for level in xrange(2, 2 + 2*height, 2):
            chain[level][level + 1] += 1

        self.size += 1
        if self.size > 1 << (height + 1):
            MAY, MUST, MUST_NOT = object(), object(), object()
            TOP_PTR = 2 + 2*(height-1)
            TOP_SPAN = TOP_PTR + 1
            NEW_PTR = TOP_PTR + 2
            NEW_SPAN = TOP_SPAN + 2
            promote = MAY
            node = self.head
            node.extend([sentinel, node[TOP_SPAN]])
            prev = node
            node = node[TOP_PTR]
            while node is not sentinel:
                if promote is MAY:
                    if getrandbits(1):
                        node.extend([sentinel, node[TOP_SPAN]])
                        prev[NEW_PTR] = node
                        prev = node
                        promote = MUST_NOT
                    else:
                        prev[NEW_SPAN] += node[TOP_SPAN]
                        promote = MUST
                elif promote is MUST:
                    node.extend([sentinel, node[TOP_SPAN]])
                    prev[NEW_PTR] = node
                    prev = node
                    promote = MAY
                else: # promote is MUST_NOT
                    prev[NEW_SPAN] += node[TOP_SPAN]
                    promote = MAY
                node = node[TOP_PTR]
            self.height += 1
    append = add


    def remove(self, value):
        """Remove the argument `value` from the SkipList.
        The *first* element that compares equal to `value` is removed.
"""

        height = self.height
        sentinel = self.sentinel

        chain = [None] * (2 + 2*height)
        node = self.head
        for level in xrange(2*height, 0, -2):
            while node[level] is not sentinel \
                  and node[level][0] < value:
                node = node[level]
            chain[level] = node

        old = chain[2][2]
        if old is sentinel or chain[2][2][0] != value:
            raise ValueError("%s is not in %s" % (value, type(self).__name__))
        for level in xrange(2, len(chain[2][2]), 2):
            prev = chain[level]
            prev[level] = old[level]
            prev[level + 1] += old[level + 1]
        if old[2] is sentinel:
            self.tail = old[1]
        else:
            old[2][1] = old[1]
        for level in xrange(2, 2 + 2*height, 2):
            chain[level][level + 1] -= 1

        self.size -= 1
        if self.size < (1 << height) and height > 1:
            node = self.head
            while node is not sentinel:
                node.pop()
                node = node.pop()
            self.height -= 1


    def index(self, value):
        """Return the first index at which an object comparing equal to `value`
    can be found.
"""

        sentinel = self.sentinel
        node = self.head
        ret = 0
        for level in xrange(2*self.height, 0, -2):
            while node[level] is not sentinel \
                  and node[level][0] < value:
                ret += node[level + 1]
                node = node[level]
        node = node[2]
        if node is sentinel or node[0] != value:
            raise ValueError("%s is not in %s" % (value, type(self).__name__))
        return ret
    find = index


    def sort(self):
        """Sort the list in-place.
    Because SkipLists are always maintained in sort order, this method
    does nothing
"""

        pass


    def popleft(self):
        """Remove and return the first (least) element.
    This method is slightly more efficient than SkipList.pop(0)
    because it doesn't have to perform the SkipList scan
"""

        if not len(self):
            raise IndexError("popleft from empty %s" % type(self).__name__)
        height = self.height
        sentinel = self.sentinel
        head = self.head

        old = head[2]
        ret = old[0]
        for level in xrange(2, len(old), 2):
            head[level] = old[level]
            head[level + 1] += old[level + 1]
        if old[2] is sentinel:
            self.tail = head
        else:
            old[2][1] = head
        for level in xrange(2, 2 + 2*height, 2):
            # TODO:
            head[level + 1] -= 1

        self.size -= 1
        if self.size < (1 << height) and height > 1:
            node = self.head
            while node is not sentinel:
                node.pop()
                node = node.pop()
            self.height -= 1
        return ret


    def __getitem__(self, index):
        if index < -len(self):
            raise IndexError("%s index out of range" % type(self).__name__)
        elif index < 0:
            index += len(self)

        sentinel = self.sentinel
        steps = -1
        node = self.head
        for level in xrange(2*self.height, 0, -2):
            while node[level] is not sentinel \
                  and steps + node[level + 1] < index:
                steps += node[level + 1]
                node = node[level]
        node = node[2]
        if node is sentinel:
            raise IndexError("%s index out of range" % type(self).__name__)
        return node[0]


    def pop(self, index=-1):
        """Remove and return the element at `index`
"""

        if index < -len(self):
            raise IndexError("%s index out of range" % type(self).__name__)
        elif index < 0:
            index += len(self)

        height = self.height
        sentinel = self.sentinel
        node = self.head
        steps = -1
        chain = [None] * (2 + 2*height)
        for level in xrange(2*height, 0, -2):
            while node[level] is not sentinel \
                  and steps + node[level + 1] < index:
                steps += node[level + 1]
                node = node[level]
            chain[level] = node

        old = chain[2][2]
        if old is sentinel:
            raise IndexError("%s index out of range" % type(self).__name__)
        for level in xrange(2, len(old), 2):
            prev = chain[level]
            prev[level] = old[level]
            prev[level + 1] += old[level + 1]
        if old[2] is sentinel:
            self.tail = old[1]
        else:
            old[2][1] = old[1]
        for level in xrange(2, 2*height + 2, 2):
            chain[level][level + 1] -= 1

        self.size -= 1
        if self.size < (1 << height) and height > 1:
            node = self.head
            while node is not sentinel:
                node.pop()
                node = node.pop()
            self.height -= 1
        return old[0]


    def __delitem__(self, index):
        self.pop(index)


    def __len__(self):
        return self.size


    def __iter__(self):
        sentinel = self.sentinel
        node = self.head[2]
        while node is not sentinel:
            yield node[0]
            node = node[2]


    def __reversed__(self):
        head = self.head
        node = self.tail
        while node is not head:
            yield node[0]
            node = node[1]


    def __repr__(self):
        return "%s.%s(%s)" % (__name__, type(self).__name__, list(self))


    def __del__(self):
        # break the reference cycle formed by the reverse pointers
        node = self.head
        sentinel = self.sentinel
        while node is not sentinel:
            node[1] = None
            node = node[2]


    def preen(self):
        """In the unlikely event that a SkipList's distribution of element levels
    is causing pathological performance (either in space or time),
    SkipList.preen() will rebuild those levels and restore the
    SkipList's expected performance.
"""

        height = self.height
        sentinel = self.sentinel
        head = self.head

        MAY, MUST, MUST_NOT = object(), object(), object()
        promote = [None] * 4 + [MAY,  None] * (height-1)
        chain   = [None] * 4 + [head,    0] * (height-1)
        node = head[2]
        while node is not sentinel:
            for level in xrange(4, 2 + 2*height, 2):
                # TODO:
                chain[level + 1] += 1
            for level in xrange(4, 2 + 2*height, 2):
                if promote[level] is MAY:
                    if getrandbits(1):
                        prev = chain[level]
                        prev[level:] = [node, chain[level + 1]]
                        chain[level:level + 2] = [node, 0]
                        promote[level] = MUST_NOT
                    else:
                        promote[level] = MUST
                        del node[level:]
                        break
                elif promote[level] is MUST:
                    prev = chain[level]
                    prev[level:] = [node, chain[level + 1]]
                    chain[level:level + 2] = [node, 0]
                    promote[level] = MAY
                else: # promote[level] is MUST_NOT
                    promote[level] = MAY
                    del node[level:]
                    break
            node = node[2]
        for level in xrange(4, 2 + 2*height, 2):
            chain[level][level:] = [sentinel, chain[level + 1] + 1]


    @property
    def levels(self):
        sentinel = self.sentinel
        node = self.head[2]
        while node is not sentinel:
            yield (len(node) - 2) // 2
            node = node[2]


__all__ = [ 'SkipList' ]



if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print "Usage: %s test_size" % sys.argv[0]

    from random import randrange, sample, shuffle, choice
    from math import ceil
    from bisect import bisect_left, insort_left
    from itertools import imap
    from operator import eq
    test_size = int(sys.argv[1])

    def create_test_lists(max_elem, list_size):
        print >>sys.stderr, "Creating a SkipList with %d random elements less than %d" % (list_size, max_elem)
        a = SkipList()
        b = []
        for e in ( randrange(max_elem*2) for _ in xrange(list_size) ):
            a.add(e)
            b.append(e)
        b.sort()
        return (a, b)

    def check_SkipList(sl, l):
        s = frozenset(l)
        print >>sys.stderr, "checking"
        if not all(imap(eq, l, sl)):
            raise RuntimeError('SkipList and test list do not have the same content')
        if not all(imap(eq, reversed(l), reversed(sl))):
            raise RuntimeError('SkipList reversed iterator is broken')
        if not [ sl[i] for i in xrange(len(l)) ] == l:
            raise RuntimeError('SkipList __getitem__ is broken')
        if not all(sl.index(v) == bisect_left(l, v) for v in s):
            raise RuntimeError('SkipList index is broken')
        print >>sys.stderr, "preening"
        sl.preen()
        print >>sys.stderr, "checking"
        if not all(imap(eq, l, sl)):
            raise RuntimeError('SkipList and test list do not have the same content')
        if not all(imap(eq, reversed(l), reversed(sl))):
            raise RuntimeError('SkipList reversed iterator is broken')
        if not [ sl[i] for i in xrange(len(l)) ] == l:
            raise RuntimeError('SkipList __getitem__ is broken')
        if not all(sl.index(v) == bisect_left(l, v) for v in s):
            raise RuntimeError('SkipList index is broken')


    print >>sys.stderr, "Testing deletion by index"
    a, b = create_test_lists(test_size*2, test_size)
    check_SkipList(a, b)

    while a:
        delete_count = int(ceil(len(a) / 2.))
        print >>sys.stderr, "Deleting %d indexes (%d remain)" % (delete_count, len(a) - delete_count)
        for _ in xrange(delete_count):
            i = randrange(len(b))
            del a[i]
            del b[i]
        check_SkipList(a, b)

    print >>sys.stderr, "Testing deletion by value"
    a, b = create_test_lists(test_size*2, test_size)
    check_SkipList(a, b)

    while a:
        delete_count = int(ceil(len(a) / 2.))
        print >>sys.stderr, "Deleting %d elements (%d remain)" % (delete_count, len(a) - delete_count)
        population = sample(b, delete_count)
        shuffle(population)
        for elem in population:
            a.remove(elem)
            del b[bisect_left(b, elem)]
        check_SkipList(a, b)


    print >>sys.stderr, "Testing mixed insertion, deletion by index, and deletion by value"
    a, b = create_test_lists(test_size*2, test_size//2)
    check_SkipList(a, b)
    report = [0, 0, 0]
    for _ in xrange(test_size//2):
        what = getrandbits(2)
        if what == 0 or what == 1:
            e = randrange(test_size*2)
            a.add(e)
            insort_left(b, e)
            report[0] += 1
        elif what == 2:
            i = randrange(len(b))
            del a[i]
            del b[i]
            report[1] += 1
        else: # what == 3
            e = choice(b)
            a.remove(e)
            del b[bisect_left(b, e)]
            report[2] += 1
    print "Performed %d insertions, %d deletions by index, and %d deletions by value" % tuple(report)
    check_SkipList(a, b)

    print >>sys.stderr, "Tests passed!"
