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


from localdata import LocalList
from decorator_decorator import decorator_decorator

@decorator_decorator
def shadowstack(f):
    """Builds a shadow stack for its argument.
    This side-steps python's relatively small stack for functions that are not
    tail-recursive, but are naturally expressed through recursion.
    This will not optimize the memory usage of your program. It only keeps
    python's natural stack from overflowing.
    If you want to optimize the memory usage of your program, rewrite
    it so that it is tail-recursive and then use the tco module.
    For a single recursion, the function may be called multiple time with the
    same set of arguments. This is especially true if the function is multiply
    recursive.

    shadowstack is intended for use as a decorator. e.g.
    @shadowstack
    def foo(*args, **kwargs):
        ...
    """
    class RecursionException(BaseException):
        pass

    pending = LocalList()

    def shadowstacked(*args, **kwargs):
        if pending:
            try:
                return pending[-1][2][(args, frozenset(kwargs.iteritems()))]
            except KeyError:
                raise RecursionException(args, kwargs)
            # We don't catch TypeError because if the arguments are unhashable,
            # we'll just spin forever.
        else:
            pending.append((args, kwargs, {}))
            try:
                while pending:
                    args, kwargs = pending[-1][:2]

                    try:
                        retval = f(*args, **kwargs)
                    except RecursionException as e:
                        assert len(e.args) == 2
                        args, kwargs = e.args
                        del e
                        pending.append((args, kwargs, {}))
                    else:
                        pending.pop()
                        if pending:
                            pending[-1][2][(args, frozenset(kwargs.iteritems()))] = retval
                return retval
            finally:
                del pending[:]
    return shadowstacked

__all__ = ['shadowstack']

import callable_module
callable_module(shadowstack)
