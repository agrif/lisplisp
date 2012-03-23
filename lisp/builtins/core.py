from .procedure import builtin_full, builtin, BuiltinFull, parse_arguments
from ..types import InvalidValue, Symbol, Cell, String, Procedure
from ..eval import EvalException, CommonContinuation, EvalState, EvalListState
from ..scope import Scope, NameNotSet
from ..parser import parse

from pypy.rlib.jit import unroll_safe

@builtin_full('quote')
class Quote(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, _ = parse_arguments(args, 1)
        return continuation.next(req[0])

@builtin_full('eval')
class Eval(BuiltinFull):
    def call(self, scope, args, continuation):
        _, _, rest = parse_arguments(args, 0, 0, True)
        self.length = len(rest)
        self.unevaluated = rest
        self.evaluated = [None] * self.length
        self.scope = scope
        self.continuation = continuation
        
        if self.length == 0:
            return self.continuation.next(None)
        return EvalState(scope, self.unevaluated[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        self.evaluated[i] = result
        
        if i + 1 >= self.length:
            # this is the end, now evaluate them all again
            return EvalListState(self.scope, self.evaluated, self.continuation)
        # keep going
        return EvalState(self.scope, self.unevaluated[i + 1], CommonContinuation(self, i + 1))

# @unroll_safe
# def _l_set(scope, args, eval_symbol):
#     _, _, rest = parse_arguments(args, 0, 0, True)
    
#     if len(rest) % 2 != 0:
#         raise EvalException("set requires an even number of arguments")
    
#     i = 0
#     value = None
#     while i < len(rest):
#         symbol = rest[i]
#         orig_symbol = symbol
#         if eval_symbol:
#             symbol = eval(scope, symbol)
#         value = eval(scope, rest[i + 1])
        
#         if not isinstance(symbol, Symbol):
#             raise EvalException("value is not a symbol", orig_symbol)
        
#         scope.set(symbol.name, value)
        
#         i += 2
#     return value

# @procedure('set')
# def l_set(scope, args):
#     return _l_set(scope, args, True)

# @procedure('setq')
# def l_setq(scope, args):
#     return _l_set(scope, args, False)

@builtin_full('set-p')
class SetP(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, _ = parse_arguments(args, 1)
        self.continuation = continuation
        self.scope = scope
        self.orig_symbol = req[0]
        return EvalState(scope, req[0], CommonContinuation(self, 0))
    def got_result(self, unused, symbol):
        if not isinstance(symbol, Symbol):
            raise EvalException("value is not a symbol", self.orig_symbol)
        if self.scope.is_set(symbol.name):
            return self.continuation.next(Symbol('t'))
        return self.continuation.next(None)

# @procedure('let')
# @unroll_safe
# def l_let(scope, args):
#     req, _, rest = parse_arguments(args, 1, 0, True)
#     if not isinstance(req[0], Cell):
#         raise EvalException("let bindings are not a list")
#     try:
#         bindings = req[0].to_list()
#     except InvalidValue:
#         raise EvalException("let bindings are not a list")
    
#     bindings_cached = {}
#     for binding in bindings:
#         orig_binding = binding
#         if not isinstance(binding, Cell):
#             raise EvalException("let binding is not a 2-list", orig_binding)
#         symbol = binding.car
#         binding = binding.cdr
#         if not isinstance(symbol, Symbol):
#             raise EvalException("let binding name is not a symbol", orig_binding)
#         if not isinstance(binding, Cell):
#             raise EvalException("let binding is not a 2-list", orig_binding)
#         value = binding.car
#         if binding.cdr is not None:
#             raise EvalException("let binding is not a 2-list", orig_binding)
#         value = eval(scope, value)
#         bindings_cached[symbol.name] = value
    
#     newscope = Scope(scope)
#     for name, val in bindings_cached.items():
#         newscope.set(name, val, local_only=True)
#     return eval_list(newscope, rest)

# @procedure('throw')
# def l_throw(scope, args):
#     req, _, _ = parse_arguments(args, 1)
#     error = eval(scope, req[0])
#     if not isinstance(error, String):
#         raise EvalException("error is not a string")
#     raise EvalException(error.data)

# @procedure('catch')
# @unroll_safe
# def l_catch(scope, args):
#     req, _, rest = parse_arguments(args, 1, 0, True)
#     handler = eval(scope, req[0])
#     if not isinstance(handler, Procedure):
#         raise EvalException("handler is not a procedure")
#     ret = None
#     try:
#         ret = eval_list(scope, rest)
#     except EvalException, e:
#         message = e.message
#         trace = list(e.trace)
#         trace.reverse()
#         trace_lisp = None
#         for sexp in trace:
#             trace_lisp = Cell(sexp, trace_lisp)
#         args = Cell(String(message), Cell(Cell(Symbol('quote'), Cell(trace_lisp))))
#         ret = eval(scope, Cell(handler, args))
#     return ret

@builtin('parse', 1)
def l_parse(req, opt, rest):
    s = req[0]
    if not isinstance(s, String):
        raise EvalException("argument is not a string")
    parsed = parse(s.data)
    if isinstance(parsed, Cell) and parsed.cdr is None:
        return parsed.car
    return parsed

@builtin('unparse', 1)
def l_unparse(req, opt, rest):
    if req[0] is None:
        return String('nil')
    return String(req[0].unparse())

@builtin_full('begin')
class Begin(BuiltinFull):
    def call(self, scope, args, continuation):
        _, _, rest = parse_arguments(args, 0, 0, True)
        return EvalListState(scope, rest, continuation)

@builtin_full('and')
class And(BuiltinFull):
    def call(self, scope, args, continuation):
        _, _, self.args = parse_arguments(args, 0, 0, True)
        self.num_args = len(self.args)
        self.scope = scope
        self.continuation = continuation
        
        if self.num_args == 0:
            # default true
            return continuation.next(Symbol('t'))
        return EvalState(scope, self.args[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        # if this is the end, return
        if i + 1 >= self.num_args:
            return self.continuation.next(result)
        # if even one is nil, return nil
        if result is None:
            return self.continuation.next(None)
        
        # evaluate the next one
        return EvalState(self.scope, self.args[i + 1], CommonContinuation(self, i + 1))

@builtin_full('or')
class Or(BuiltinFull):
    def call(self, scope, args, continuation):
        _, _, self.args = parse_arguments(args, 0, 0, True)
        self.num_args = len(self.args)
        self.scope = scope
        self.continuation = continuation
        
        if self.num_args == 0:
            # default nil
            return continuation.next(None)
        return EvalState(scope, self.args[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        # if this is the end, return
        if i + 1 >= self.num_args:
            return self.continuation.next(result)
        # if even one is true, return it
        if result is not None:
            return self.continuation.next(result)
        
        # evaluate the next one
        return EvalState(self.scope, self.args[i + 1], CommonContinuation(self, i + 1))

@builtin_full('if')
class If(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, rest = parse_arguments(args, 2, 0, True)
        self.if_true = [req[1]]
        self.if_false = rest
        self.scope = scope
        self.continuation = continuation
        # evaluate the test
        return EvalState(scope, req[0], CommonContinuation(self, 0))
    def got_result(self, unused, result):
        if result is None:
            # false
            return EvalListState(self.scope, self.if_false, self.continuation)
        else:
            # true
            return EvalListState(self.scope, self.if_true, self.continuation)

@builtin_full('while')
class While(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, rest = parse_arguments(args, 1, 0, True)
        self.test = req[0]
        self.body = rest
        self.scope = scope
        self.continuation = continuation
        return self.got_result(0, None)
    def got_result(self, mode, result):
        if mode == 0:
            # test mode
            return EvalState(self.scope, self.test, CommonContinuation(self, 1))
        elif mode == 1:
            # body mode
            # if it's false, just return
            if result is None:
                return self.continuation.next(None)
            # do the loop otherwise, come back in test mode
            return EvalListState(self.scope, self.body, CommonContinuation(self, 0))
