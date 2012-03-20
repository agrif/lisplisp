from .procedure import procedure, parse_arguments
from ..types import InvalidValue, Symbol, Cell, String, Procedure
from ..eval import EvalException, eval, eval_list, eval_list_each
from ..scope import Scope, NameNotSet
from ..parser import parse

from pypy.rlib.jit import unroll_safe

@procedure('quote')
def l_quote(scope, args):
    req, _, _ = parse_arguments(args, 1)
    return req[0]

@procedure('eval')
def l_eval(scope, args):
    _, _, rest = parse_arguments(args, 0, 0, True)
    return eval_list(scope, eval_list_each(scope, rest))

@unroll_safe
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
    if scope.is_set(symbol.name):
        return Symbol('t')
    return None

@procedure('let')
@unroll_safe
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
    
    newscope = Scope(scope)
    for name, val in bindings_cached.items():
        newscope.set(name, val, local_only=True)
    return eval_list(newscope, rest)

@procedure('throw')
def l_throw(scope, args):
    req, _, _ = parse_arguments(args, 1)
    error = eval(scope, req[0])
    if not isinstance(error, String):
        raise EvalException("error is not a string")
    raise EvalException(error.data)

@procedure('catch')
@unroll_safe
def l_catch(scope, args):
    req, _, rest = parse_arguments(args, 1, 0, True)
    handler = eval(scope, req[0])
    if not isinstance(handler, Procedure):
        raise EvalException("handler is not a procedure")
    ret = None
    try:
        ret = eval_list(scope, rest)
    except EvalException, e:
        message = e.message
        trace = list(e.trace)
        trace.reverse()
        trace_lisp = None
        for sexp in trace:
            trace_lisp = Cell(sexp, trace_lisp)
        args = Cell(String(message), Cell(Cell(Symbol('quote'), Cell(trace_lisp))))
        ret = eval(scope, Cell(handler, args))
    return ret

@procedure('parse')
def l_parse(scope, args):
    req, _, _ = parse_arguments(args, 1)
    s = eval(scope, req[0])
    if not isinstance(s, String):
        raise EvalException("argument is not a string")
    parsed = parse(s.data)
    if isinstance(parsed, Cell) and parsed.cdr is None:
        return parsed.car
    return parsed

@procedure('unparse')
def l_unparse(scope, args):
    req, _, _ = parse_arguments(args, 1)
    val = eval(scope, req[0])
    if val is None:
        return String('nil')
    return String(val.unparse())

@procedure('begin')
def l_begin(scope, args):
    _, _, rest = parse_arguments(args, 0, 0, True)
    return eval_list(scope, rest)

@procedure('if')
def l_if(scope, args):
    req, _, rest = parse_arguments(args, 2, 0, True)
    testval = eval(scope, req[0])
    if testval is not None:
        return eval(scope, req[1])
    return eval_list(scope, rest)

@procedure('while')
def l_while(scope, args):
    req, _, rest = parse_arguments(args, 1, 0, True)
    test = req[0]
    while eval(scope, test) is not None:
        eval_list(scope, rest)
    return None
