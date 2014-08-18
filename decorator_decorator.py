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
