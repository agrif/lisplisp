from .procedure import procedure, parse_arguments
from ..types import Number, Integer, Float
from ..eval import EvalException, eval

@procedure('+')
def l_add(scope, args):
    _, _, rest = parse_arguments(args, 0, 0, True)
    use_float = False
    summands = []
    for sexp in rest:
        val = eval(scope, sexp)
        if not isinstance(val, Number):
            raise EvalException('value not a number', sexp)
        if isinstance(val, Float):
            use_float = True
        summands.append(val)
    if use_float:
        gather_float = 0.0
        for val in summands:
            gather_float += val.get_float()
        return Float(gather_float)
    gather = 0
    for val in summands:
        assert isinstance(val, Integer)
        gather += val.value
    return Integer(gather)

@procedure('*')
def l_multiply(scope, args):
    _, _, rest = parse_arguments(args, 0, 0, True)
    use_float = False
    terms = []
    for sexp in rest:
        val = eval(scope, sexp)
        if not isinstance(val, Number):
            raise EvalException('value not a number', sexp)
        if isinstance(val, Float):
            use_float = True
        terms.append(val)
    if use_float:
        gather_float = 1.0
        for val in terms:
            gather_float *= val.get_float()
        return Float(gather_float)
    gather = 1
    for val in terms:
        assert isinstance(val, Integer)
        gather *= val.value
    return Integer(gather)

@procedure('-')
def l_subtract(scope, args):
    req, opt, _ = parse_arguments(args, 1, 1)
    val1 = eval(scope, req[0])
    if not isinstance(val1, Number):
        raise EvalException('value not a number', req[0])
    if len(opt) == 0:
        assert isinstance(val1, Integer) or isinstance(val1, Float)
        if isinstance(val1, Integer):
            return Integer(-val1.value)
        if isinstance(val1, Float):
            return Float(-val1.value)
    else:
        val2 = eval(scope, opt[0])
        if not isinstance(val2, Number):
            raise EvalException('value not a number', opt[0])
        if isinstance(val1, Float) or isinstance(val2, Float):
            return Float(val1.get_float() - val2.get_float())
        assert isinstance(val1, Integer) and isinstance(val2, Integer)
        return Integer(val1.value - val2.value)

@procedure('/')
def l_divide(scope, args):
    req, opt, _ = parse_arguments(args, 1, 1)
    val1 = eval(scope, req[0])
    if not isinstance(val1, Number):
        raise EvalException('value not a number', req[0])
    if len(opt) == 0:
        return Float(1.0 / val1.get_float())
    else:
        val2 = eval(scope, opt[0])
        if not isinstance(val2, Number):
            raise EvalException('value not a number', opt[0])
        return Float(val1.get_float() / val2.get_float())
