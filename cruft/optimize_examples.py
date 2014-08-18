def ident(x):
    return x

def if_then_else(x):
    if x is None:
        return 1
    elif x == 0:
        return 2
    else:
        return 3
    return 4

def parallel_assignment0(a,b,c,d,e,f,g):
    a[:], b[:], c[:], d[:], e[:], f[:], g[:] = g[:], a[:], b[:], c[:], d[:], e[:], f[:]

def parallel_assignment1(a,b,c,d,e,f,g):
    a[:], b[:], c[:], d[:], e[:], f[:], g[:] = b[:], c[:], d[:], e[:], f[:], g[:], a[:]

def parallel_assignment2(a,b,c,d,e,f,g):
    g[:], a[:], b[:], c[:], d[:], e[:], f[:]  = a[:], b[:], c[:], d[:], e[:], f[:], g[:]

def parallel_assignment3(a,b,c,d,e,f,g):
    b[:], c[:], d[:], e[:], f[:], g[:], a[:]  = a[:], b[:], c[:], d[:], e[:], f[:], g[:]

def loop_continue(x):
    while x > 0:
        x -= 1
        continue
        print "Never get here"
    return x

def loop_break(x):
    while x > 0:
        x -= 1
        break
        print "Never get here"
    return x

def loop_cond_continue(x):
    while x > 0:
        x -= 1
        if x % 2 < 1:
            continue
        print "1"
    return x

def loop_cond_break(x):
    while x > 0:
        x -= 1
        if x % 2 < 1:
            break
        print "1"
    return x

def loop_finally(x):
    for i in xrange(x):
        try:
            i *= 2
        finally:
            print i

def loop_finally_continue(x):
    while True:
        try:
            continue
        finally:
            return 0

def loop_finally_break(x):
    while True:
        try:
            break
        finally:
            return 0

def break_from_finally(x):
    while True:
        try:
            pass
        finally:
            break
    return x

# not valid python
"""
def continue_from_finally(x):
    while x > 0:
        try:
            x -= 1
        finally:
            continue
"""

def except_loop(x):
    try:
        while x > 0:
            x -= 1
            if x % 2 < 1:
                break
        return x
    except AttributeError:
        return True
    except:
        return False

def finally_except_loop(x):
    try:
        while x > 0:
            x -= 1
            if x % 2 < 1:
                break
        return x
    except AttributeError:
        return True
    except:
        return False
    finally:
        return x + 1

def crazy(x):
    for i in xrange(x):
        try:
            raise Exception
        except:
            continue
        finally:
            break
    return i
