from .procedure import builtin, parse_arguments
from ..types import BoxedType, Cell, Symbol, String, Number, Integer, Float, Procedure
from ..eval import EvalException

def make_checker(name, typ):
    @builtin(name + '-p', 1)
    def inner_checker(req, opt, rest):
        if isinstance(req[0], typ):
            return Symbol('t')
        return None
    return inner_checker

make_checker('boxed', BoxedType)
make_checker('cell', Cell)
make_checker('symbol', Symbol)
make_checker('string', String)
make_checker('number', Number)
make_checker('integer', Integer)
make_checker('float', Float)
make_checker('procedure', Procedure)

@builtin('nil-p', 1)
def l_nil_p(req, opt, rest):
    if req[0] is None:
        return Symbol('t')
    return None

@builtin('cons', 2)
def l_cons(req, opt, rest):
    return Cell(req[0], req[1])

@builtin('car', 1)
def l_car(req, opt, rest):
    val = req[0]
    if not isinstance(val, Cell):
        raise EvalException("value not a cell")
    return val.car

@builtin('cdr', 1)
def l_cdr(req, opt, rest):
    val = req[0]
    if not isinstance(val, Cell):
        raise EvalException("value not a cell")
    return val.cdr

@builtin('eq', 2)
def l_eq(req, opt, rest):
    val1 = req[0]
    val2 = req[1]
    if val1 is None:
        if val2 is None:
            return Symbol('t')
        return None
    if val1.eq(val2):
        return Symbol('t')
    return None
