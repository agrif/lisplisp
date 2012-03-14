from .procedure import procedure, parse_arguments
from ..types import InvalidValue, Symbol, Cell
from ..eval import EvalException, eval
from ..scope import NameNotSet

@procedure('quote')
def l_quote(scope, args):
    req, _, _ = parse_arguments(args, 1)
    return req[0]

@procedure('eval')
def l_eval(scope, args):
    _, _, rest = parse_arguments(args, 0, 0, True)
    res = None
    for sexp in rest:
        res = eval(scope, eval(scope, sexp))
    return res

def _l_set(scope, args, eval_symbol):
    _, _, rest = parse_arguments(args, 0, 0, True)
    
    if len(rest) % 2 != 0:
        raise EvalException("set requires an even number of arguments")
    
    i = 0
    value = None
    while i < len(rest):
        symbol = rest[i]
        orig_symbol = symbol
        if eval_symbol:
            symbol = eval(scope, symbol)
        value = eval(scope, rest[i + 1])
        
        if not isinstance(symbol, Symbol):
            raise EvalException("value is not a symbol", orig_symbol)
        
        scope.set(symbol.name, value)
        
        i += 2
    return value

@procedure('set')
def l_set(scope, args):
    return _l_set(scope, args, True)

@procedure('setq')
def l_setq(scope, args):
    return _l_set(scope, args, False)

@procedure('set-p')
def l_set_p(scope, args):
    req, _, _ = parse_arguments(args, 1)
    symbol = eval(scope, req[0])
    if not isinstance(symbol, Symbol):
        raise EvalException("value is not a symbol", req[0])
    try:
        scope.get(symbol.name)
    except NameNotSet:
        return None
    return Symbol('t')

@procedure('let')
def l_let(scope, args):
    req, _, rest = parse_arguments(args, 1, 0, True)
    if not isinstance(req[0], Cell):
        raise EvalException("let bindings are not a list")
    try:
        bindings = req[0].to_list()
    except InvalidValue:
        raise EvalException("let bindings are not a list")
    
    bindings_cached = {}
    for binding in bindings:
        orig_binding = binding
        if not isinstance(binding, Cell):
            raise EvalException("let binding is not a 2-list", orig_binding)
        symbol = binding.car
        binding = binding.cdr
        if not isinstance(symbol, Symbol):
            raise EvalException("let binding name is not a symbol", orig_binding)
        if not isinstance(binding, Cell):
            raise EvalException("let binding is not a 2-list", orig_binding)
        value = binding.car
        if binding.cdr is not None:
            raise EvalException("let binding is not a 2-list", orig_binding)
        value = eval(scope, value)
        bindings_cached[symbol.name] = value
    
    ret = None
    scope.push()
    try:
        for name, val in bindings_cached.items():
            scope.set(name, val)
        for sexp in rest:
            ret = eval(scope, sexp)
    finally:
        scope.pop()
    return ret
