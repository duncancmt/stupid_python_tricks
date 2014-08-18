import sys
import inspect

from decorator_decorator import decorates
from proxy import BetterProxy

def make_module_callable(main_fn, module):
    """Replace "module" with a callable module that invokes "main_fn" when called."""
    class CallableModule(BetterProxy):
        @staticmethod
        @decorates(main_fn)
        def __call__(*args, **kwargs):
            return main_fn(*args, **kwargs)

    sys.modules[module.__name__] = CallableModule(module)

def make_me_callable(main_fn):
    """Magic function that makes the calling module a callable module with the
    argument to this function as the function that is invoked when the module is
    called."""
    # Walk the stack towards the caller until we find a frame that doesn't
    # belong to this module. Then invoke make_module_callable with the module
    # that that frame belongs to.
    this_module = sys.modules[__name__]
    frame = sys._getframe()
    module = inspect.getmodule(frame)
    while module is this_module or module is None:
        frame = frame.f_back
        module = inspect.getmodule(frame)
    return make_module_callable(main_fn, module)

__all__ = ['make_me_callable']

make_module_callable(make_me_callable, sys.modules[__name__])
