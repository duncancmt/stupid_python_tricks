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


from inspect import getargspec
from numbers import Integral
from functools import update_wrapper

class UndefinedArityError(ValueError):
    pass

# we can't use decorator_decorator here because curry is not
# signature-preserving

def curry(fn=None, numargs=0):
    """Currys a function
Returns a new function that, when called, will return either:
1) the value of the given function applied to the given arguments (if there are
     enough arguments to satisfy the function)
=== OR ===
2) the given function curried over the originally curried arguments and the
     newly given arguments (if there are not enough arguments to satisfy the
     function)
When too many arguments are supplied, the extra arguments are discarded.
Keyword arguments will never be discarded. Newly supplied keyword arguments will
shadow older arguments.

Arguments:
fn -> the function to be curried
numargs = 0 -> the number of arguments that will satisfy the function to be
     curried. If numargs is 0, curry extracts the number of arguments from
     introspection. If numargs is 0 and the function has a * or ** argument,
     curry will raise a UndefinedArityError.

curry can be used as a decorator. e.g.
@curry
def foo(arg0, arg1, arg2...):
    ...

However, it has an alternative invocation in the case that a function
is varidiac or you wish to supply "numargs":

@curry(3)
def foo(*args, **kwargs):
    ...
== or ==
@curry(numargs=3)
def foo(*args, **kwargs):
    ...
"""

    if fn is None:
        fn = numargs
    if isinstance(fn, Integral):
        def curry_with_numargs(new_fn):
            return curry(new_fn, fn)
        return curry_with_numargs

    if numargs == 0:
        argspec = getargspec(fn)
        if not (argspec[1] is None and argspec[2] is None):
            raise UndefinedArityError("Tried to automatically curry a function with * or ** args")
        numargs = len(argspec[0])

    def curry_helper(*given,**givenkeys):
        def curried_fn(*supplied,**suppliedkeys):
            numargsgiven = len(given)+len(supplied)+len(givenkeys)+len(suppliedkeys)
            new = list(given)
            new.extend(supplied)
            newkeys = givenkeys.copy()
            newkeys.update(suppliedkeys)

            if numargsgiven < numargs:
                return curry_helper(*new,**newkeys)
            elif numargsgiven == numargs:
                return fn( *new, **newkeys )
            else:
                return fn(*new[:(numargs - numargsgiven)], **newkeys )

        return update_wrapper(curried_fn, fn)
    return curry_helper()

__all__ = ['UndefinedArityError', 'curry']

import callable_module
callable_module(curry)
