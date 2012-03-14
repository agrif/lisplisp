from .procedure import procedure, parse_arguments
from ..types import Cell, Symbol, String, Number, Integer, Float, Procedure
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

@procedure('eq')
def l_eq(scope, args):
    req, _, _ = parse_arguments(args, 2)
    val1 = eval(scope, req[0])
    val2 = eval(scope, req[1])
    if val1.eq(val2):
        return Symbol('t')
    return None
