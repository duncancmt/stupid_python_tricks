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


from collections import deque
from itertools import *
from operator import *
from heapq import heappush, heappop
from memoize import weakmemoize

debug = False

class NodeParent(object):
    def __init__(self, state, parent, op):
        self.state=state
        self.parent=parent
        self.op=op
        self.receiver()

    def expand(self):
        for op in self.operators:
            type(self)(self.successor(op), self, op)
    
def generic_classfactory(successor, is_goal, operators, receiver, namespace):
    namespace['__slots__'] = ['state', 'parent', 'op']
    namespace['successor'] = lambda self, op: successor(self.state, op)
    namespace['is_goal'] = property(lambda self: is_goal(self.state))
    namespace['operators'] = property(lambda self: operators(self.state))
    namespace['receiver'] = lambda self: receiver(self)

    return type('Node',(NodeParent,),namespace)

def generic_search(schedule_length, add_to_schedule, get_next_from_schedule,
                   classfactory, root_state, successor, is_goal, operators):
    def check_visited_and_add(node):
        if debug:
            print "adding:"
            print "\tparent:\t",(node.parent.state if node.parent else None)
            print "\top:\t",node.op
            print "\tstate:\t",node.state
        n = node.parent
        while n is not None:
            if n.state == node.state:
                return
            n = n.parent
        add_to_schedule(node)

    Node = classfactory(successor, is_goal, operators, check_visited_and_add, {})
    Node(root_state, None, None)

    while schedule_length() > 0:
        n = get_next_from_schedule()
        if debug:
            print "expanding:"
            print "\tstate:\t",n.state
        if n.is_goal:
            retval = []
            while n is not None:
                retval.append((n.state,n.op))
                n = n.parent
            return retval
        n.expand()
    return None

def dfs(root_state, successor, is_goal, operators):
    schedule = list()
    return generic_search(schedule.__len__, schedule.append, schedule.pop,
                          generic_classfactory,
                          root_state, successor, is_goal, operators)

def bfs(root_state, successor, is_goal, operators):
    schedule = deque()
    return generic_search(schedule.__len__, schedule.append, schedule.popleft,
                          generic_classfactory,
                          root_state, successor, is_goal, operators)

def ucs(root_state, successor, is_goal, operators, cost):
    schedule = list()
    def add_to_schedule(node):
        # python2's scoping rules are asinine
        heappush(schedule, (node.cost, add_to_schedule.pushcount, node))
        add_to_schedule.pushcount += 1
    add_to_schedule.pushcount = 0
    def get_next_from_schedule():
        return heappop(schedule)[-1]

    def classfactory(successor, is_goal, operators, receiver, namespace):
        namespace['cost'] = property(
                              weakmemoize(
                                lambda self:
                                  cost(self.parent.state
                                         if self.parent is not None
                                         else None,
                                       self.op, self.state) \
                                  + (self.parent.cost
                                       if self.parent is not None
                                       else 0)))
        return generic_classfactory(successor, is_goal, operators, receiver, namespace)

    return generic_search(schedule.__len__, add_to_schedule, get_next_from_schedule,
                          classfactory, root_state, successor, is_goal, operators)


__all__ = ['dfs', 'bfs', 'ucs']
