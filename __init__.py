import sys
import types

from .astprettier import pprint, pformat

class CallableModule(types.ModuleType):
    def __call__(self, *args, **kwargs):
        return pprint(*args, **kwargs)

# Allow to do astprettier('x')
sys.modules[__name__].__class__ = CallableModule
# Allow to do astprettier.print('x')
sys.modules[__name__].print = pprint
