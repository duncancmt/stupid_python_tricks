from collections import deque
from itertools import *
from operator import *
from heapq import heappush, heappop

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

def node_classfactory(successor, is_goal, operators, receiver):
    namespace = {'__slots__':['state', 'parent', 'op']}
    
    namespace['successor'] = lambda self, op: successor(self.state, op)
    namespace['is_goal'] = property(lambda self: is_goal(self.state))
    namespace['operators'] = property(lambda self: operators(self.state))
    namespace['receiver'] = lambda self: receiver(self)

    return type('Node',(NodeParent,),namespace)

def generic_search(schedule_length, add_to_schedule, get_next_from_schedule,
                   root_state, successor, is_goal, operators):
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

    Node = node_classfactory(successor, is_goal, operators, check_visited_and_add)
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
                          root_state, successor, is_goal, operators)

def bfs(root_state, successor, is_goal, operators):
    schedule = deque()
    return generic_search(schedule.__len__, schedule.append, schedule.popleft,
                          root_state, successor, is_goal, operators)

def ucs(root_state, successor, is_goal, operators, cost):
    schedule = list()
    def add_to_schedule(node):
        # python2's scoping rules are asinine
        heappush(schedule, (cost(node.state), add_to_schedule.pushcount, node))
        add_to_schedule.pushcount += 1
    add_to_schedule.pushcount = 0
    def get_next_from_schedule():
        return heappop(schedule)[-1]
    return generic_search(schedule.__len__, add_to_schedule, get_next_from_schedule,
                          root_state, successor, is_goal, operators)


__all__ = ['dfs', 'bfs', 'ucs']
