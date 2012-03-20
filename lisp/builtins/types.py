from .procedure import procedure, parse_arguments
from ..types import BoxedType, Cell, Symbol, String, Number, Integer, Float, Procedure
from ..eval import EvalException, eval

def make_checker(name, typ):
    @procedure(name + '-p')
    def inner_checker(scope, args):
        req, _, _ = parse_arguments(args, 1)
        val = eval(scope, req[0])
        if isinstance(val, typ):
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

@procedure('nil-p')
def l_nil_p(scope, args):
    req, _, _ = parse_arguments(args, 1)
    val = eval(scope, req[0])
    if val is None:
        return Symbol('t')
    return None

@procedure('cons')
def l_cons(scope, args):
    req, _, _ = parse_arguments(args, 2)
    val1 = eval(scope, req[0])
    val2 = eval(scope, req[1])
    return Cell(val1, val2)

@procedure('car')
def l_car(scope, args):
    req, _, _ = parse_arguments(args, 1)
    val = eval(scope, req[0])
    if not isinstance(val, Cell):
        raise EvalException("value not a cell", req[0])
    return val.car

@procedure('cdr')
def l_cdr(scope, args):
    req, _, _ = parse_arguments(args, 1)
    val = eval(scope, req[0])
    if not isinstance(val, Cell):
        raise EvalException("value not a cell", req[0])
    return val.cdr

@procedure('eq')
def l_eq(scope, args):
    req, _, _ = parse_arguments(args, 2)
    val1 = eval(scope, req[0])
    val2 = eval(scope, req[1])
    if val1 is None:
        if val2 is None:
            return Symbol('t')
        return None
    if val1.eq(val2):
        return Symbol('t')
    return None
