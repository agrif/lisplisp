from .procedure import builtin, parse_arguments
from ..types import Number, Integer, Float, Symbol
from ..eval import EvalException

from pypy.rlib.jit import unroll_safe

@builtin('+', 0, 0, True)
@unroll_safe
def l_add(req, opt, rest):
    use_float = False
    for sexp in rest:
        if not isinstance(sexp, Number):
            raise EvalException('value not a number')
        if isinstance(sexp, Float):
            use_float = True
    if use_float:
        gather_float = 0.0
        for val in rest:
            gather_float += val.get_float()
        return Float(gather_float)
    gather = 0
    for val in rest:
        assert isinstance(val, Integer)
        gather += val.value
    return Integer(gather)

@builtin('*', 0, 0, True)
@unroll_safe
def l_multiply(req, opt, rest):
    use_float = False
    for sexp in rest:
        if not isinstance(sexp, Number):
            raise EvalException('value not a number', sexp)
        if isinstance(sexp, Float):
            use_float = True
    if use_float:
        gather_float = 1.0
        for val in rest:
            gather_float *= val.get_float()
        return Float(gather_float)
    gather = 1
    for val in rest:
        assert isinstance(val, Integer)
        gather *= val.value
    return Integer(gather)

@builtin('-', 1, 1)
def l_subtract(req, opt, rest):
    val1 = req[0]
    if not isinstance(val1, Number):
        raise EvalException('value not a number')
    if len(opt) == 0:
        assert isinstance(val1, Integer) or isinstance(val1, Float)
        if isinstance(val1, Integer):
            return Integer(-val1.value)
        if isinstance(val1, Float):
            return Float(-val1.value)
    else:
        val2 = opt[0]
        if not isinstance(val2, Number):
            raise EvalException('value not a number')
        if isinstance(val1, Float) or isinstance(val2, Float):
            return Float(val1.get_float() - val2.get_float())
        assert isinstance(val1, Integer) and isinstance(val2, Integer)
        return Integer(val1.value - val2.value)

@builtin('/', 1, 1)
def l_divide(req, opt, rest):
    val1 = req[0]
    if not isinstance(val1, Number):
        raise EvalException('value not a number')
    if len(opt) == 0:
        if isinstance(val1, Integer) and (val1.value == 1 or val1.value == -1):
            return Integer(1 / val1.value)
        return Float(1.0 / val1.get_float())
    else:
        val2 = opt[0]
        if not isinstance(val2, Number):
            raise EvalException('value not a number')
        if isinstance(val1, Integer) and isinstance(val2, Integer):
            if val2.value * (val1.value / val2.value) == val1.value:
                return Integer(val1.value / val2.value)
        return Float(val1.get_float() / val2.get_float())

@builtin('>', 2)
def l_greater_than(req, opt, rest):
    val1 = req[0]
    if not isinstance(val1, Number):
        raise EvalException('value is not a number')
    val2 = req[1]
    if not isinstance(val2, Number):
        raise EvalException('value is not a number')
    if val1.get_float() > val2.get_float():
        return Symbol('t')
    return None

@builtin('<', 2)
def l_less_than(req, opt, rest):
    val1 = req[0]
    if not isinstance(val1, Number):
        raise EvalException('value is not a number')
    val2 = req[1]
    if not isinstance(val2, Number):
        raise EvalException('value is not a number')
    if val1.get_float() < val2.get_float():
        return Symbol('t')
    return None
