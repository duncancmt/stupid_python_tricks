"""WARNING WARNING WARNING WARNING WARNING WARNING WARNING

This TCO implementation works by directly inspecting python opcodes. This is a
brittle approach and is not guaranteed to work between python versions.  You
have been warned.

WARNING WARNING WARNING WARNING WARNING WARNING WARNING
"""

import decorator
import sys
import dis
from threading import local
from collections import Callable
from itertools import imap

def decorator_apply(dec, func, args, kwargs):
    """
    Decorate a function by preserving the signature even if dec
    is not a signature-preserving decorator.
    """
    return decorator.FunctionMaker.create(
        func, 'return decorated(%(signature)s)',
        dict(decorated=dec(func, *args, **kwargs)), __wrapped__=func)

@decorator.decorator
def decorator_decorator(dec, func, *args, **kwargs):
    """Decorator for decorators"""
    if isinstance(func, Callable):
        return decorator_apply(dec, func, args, kwargs)
    else:
        return dec(func, *args, **kwargs)

class OncePerThread(object):
    """OncePerThread is a context manager that ensures that its block is only
    entered once per thread per OncePerThread instance. You can think of this as
    the opposite of threading.RLock. It allows other threads to enter the
    protected block, but prevents reentry from the same thread.

    The attribute `entered' is True when the current thread already has a block
    protected by this OncePerThread instance.
    The attribute `owner' is the frame object containing the block protected by
    this OncePerThread instance.
    The attribute `frames_to_owner' yields the frames between the calling frame
    and the owner frame, not including either end point.
    """
    def __init__(self, exc):
        self.exc = exc
        self.local_storage = local()

    def __enter__(self):
        if self.entered:
            raise self.exc
        self.entered = True
        self.owner = sys._getframe().f_back

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.entered
        self.entered = False
        del self.owner

    @property
    def entered(self):
        try:
            return self.local_storage.entered
        except AttributeError:
            self.entered = False
            return self.entered
    @entered.setter
    def entered(self, value):
        self.local_storage.entered = value

    @property
    def owner(self):
        return self.local_storage.owner
    @owner.setter
    def owner(self, value):
        self.local_storage.owner = value
    @owner.deleter
    def owner(self):
        del self.local_storage.owner

    @property
    def frames_to_owner(self):
        frame = sys._getframe().f_back.f_back
        while frame is not self.owner:
            yield frame
            frame = frame.f_back


@decorator_decorator
def tail_call_optimize(f):
    """tail_call_optimize performs tail-call optimization when its argument is a
    tail-recursive function.

    Non-tail-call recursion will not be optimized.
    This is not a particularly high-performance optimization because it both
    abuses python's exception system and uses direct bytecode
    inspection. However, tail_call_optimize will ensure that memory usage of a
    tail-recursive function is bounded by a constant and that the stack will not
    overflow.
    """
    
    class TailRecursionException(BaseException):
        pass

    class AlreadyCalledError(BaseException):
        pass

    lock = OncePerThread(AlreadyCalledError)

    def tail_call_optimized(*args, **kwargs):
        try:
            with lock:
                while True:
                    try:
                        return f(*args, **kwargs)
                    except TailRecursionException as e:
                        assert len(e.args) == 2
                        args = e.args[0]
                        kwargs = e.args[1]
        except AlreadyCalledError:
            if all(imap(lambda frame: ord(frame.f_code.co_code[frame.f_lasti+3]) \
                                          == dis.opmap['RETURN_VALUE'],
                        lock.frames_to_owner)):
                # We check each frame from the frame calling the TCO'd function
                # up to (not including, although it wouldn't matter) the other
                # tail_call_optimized frame. We check to make sure that the next
                # instruction in each of those frames is a RETURN_VALUE. We skip
                # ahead 3 instructions instead of 1 because the 2 bytes that
                # come after the CALL_FUNCTION* instruction are the argument to
                # that instruction.
                raise TailRecursionException(args, kwargs)
            else:
                return f(*args, **kwargs)

    return tail_call_optimized

tail_call_optimized = tail_call_optimize
tco = tail_call_optimize
tcod = tail_call_optimize

__all__ = ["tail_call_optimize", "tail_call_optimized", "tco", "tcod"]


if __name__ == '__main__':
    tco = sys.modules[__name__]
    @tco.tail_call_optimize
    def fact(n, accum=1):
        return accum if n == 0 else fact(n-1, accum*n)
    print "tail-recursive factorial\nfactorial(7) = %d" % fact(7)
    print "factorial(100) = %d" % fact(100)
    print "factorial(1000) = %d" % fact(1000)

    @tco.tail_call_optimize
    def stupid_fact(n, accum=1):
        def helper(*args, **kwargs):
            return stupid_fact(*args, **kwargs)
        return accum if n == 0 else helper(n-1, accum*n)

    print "\n\nmutually tail-recursive factorial\nfactorial(7) = %d" % stupid_fact(7)
    print "factorial(100) = %d" % stupid_fact(100)
    print "factorial(1000) = %d" % stupid_fact(1000)

    @tco.tail_call_optimize
    def naive_fact(n):
        return 1 if n == 0 else n * naive_fact(n-1)

    print "\n\nnon-tail-recursive factorial\nfactorial(7) = %d" % naive_fact(7)
    print "factorial(100) = %d" % naive_fact(100)
    try:
        print "factorial(1000) = %d" % naive_fact(1000)
        print "that should've thrown an error :("
    except RuntimeError:
        print "factorial(1000) overflows the stack"


    import timeit
    def fact_iterative(n):
        accum = 1
        while n > 0:
            accum *= n
            n -= 1
        return accum

    print '\n\niterative factorial timing'
    iterative_time = timeit.timeit(stmt='fact_iterative(1000)',
                                   setup='from __main__ import fact_iterative',
                                   number=10000)
    print iterative_time / 10000, 'seconds per call'

    print '\n\ntail-recursive factorial timing'
    recursive_time =  timeit.timeit(stmt='fact(1000)',
                                    setup='from __main__ import fact',
                                    number=10000)
    print recursive_time / 10000, 'seconds per call'
    print 'factor of', recursive_time / iterative_time, 'slowdown'
