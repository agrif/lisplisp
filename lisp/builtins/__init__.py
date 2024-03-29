from .procedure import register as register_procedures
from ..types import Symbol

import core
import math
import types
import io
import ffi

def register(scope):
    # idempotent symbols
    scope.set('t', Symbol('t'))
    # now procedures
    register_procedures(scope)
