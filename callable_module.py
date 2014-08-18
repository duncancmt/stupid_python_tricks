import sys
import inspect
import types
import importlib
from collections import Callable

from decorator_decorator import decorates

def make_me_callable(main_fn):
    """This function is black magic. Further docstring to come."""
    module = inspect.getmodule(sys._getframe().f_back)

    copied_attributes = [False] # python2's scoping rules are dumb

    class CallableModule(types.ModuleType):
        def __init__(self):
            try:
                doc = module.__doc__
            except AttributeError:
                super(CallableModule, self).__init__(module.__name__)
            else:
                super(CallableModule, self).__init__(module.__name__, doc)

        @staticmethod
        @decorates(main_fn)
        def __call__(*args, **kwargs):
            return main_fn(*args, **kwargs)

        def __getattr__(self, name):
            # stupid scoping rules
            if not copied_attributes[0]:
                for attr in dir(module):
                    setattr(self, attr, getattr(module, attr))
                copied_attributes[0] = True
            return getattr(module, name)

    sys.modules[module.__name__] = CallableModule()

__all__ = ['make_me_callable']
