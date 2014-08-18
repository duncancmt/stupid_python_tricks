import decorator
from collections import Callable

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

__all__ = ['decorator_decorator']
