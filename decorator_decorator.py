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


import decorator
from collections import Callable

def decorator_apply(dec, func, args, kwargs):
    """
    Decorate a function by preserving the signature even if dec
    is not a signature-preserving decorator.
    """
    return decorator.FunctionMaker.create(
        func, 'return decorated(%(signature)s)',
        dict(decorated=dec(func, *args, **kwargs)), __wrapped__=func,
        addsource=True)

@decorator.decorator
def decorator_decorator(dec, func, *args, **kwargs):
    """Decorator for decorators"""
    if isinstance(func, Callable):
        return decorator_apply(dec, func, args, kwargs)
    else:
        return dec(func, *args, **kwargs)

def decorates(dec, func=None):
    if not isinstance(func, Callable):
        def decorates_with_func(new_dec):
            return decorates(new_dec, dec)
        return decorates_with_func

    return decorator.FunctionMaker.create(
        func, 'return decorated(%(signature)s)',
        dict(decorated=dec, __wrapped__=func))

__all__ = ['decorator_decorator', 'decorates']
