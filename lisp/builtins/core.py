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

@builtin_full('set')
class Set(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, _ = parse_arguments(args, 2)
        
        self.scope = scope
        self.expression = req[1]
        self.symbol = None
        self.continuation = continuation
        return EvalState(scope, req[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        if i == 0:
            # the symbol
            self.symbol = result
            return EvalState(self.scope, self.expression, CommonContinuation(self, 1))
        
        # the expression, now we're done
        symbol = self.symbol
        if not isinstance(symbol, Symbol):
            raise EvalException("binding name is not a symbol")
        self.scope.set(symbol.name, result)
        return self.continuation.next(result)

@builtin_full('setq')
class SetQ(BuiltinFull):
    def call(self, scope, args, continuation):
        _, _, rest = parse_arguments(args, 0, 0, True)
        
        if len(rest) % 2 != 0:
            raise EvalException("setq takes an even number of arguments")
        
        self.scope = scope
        self.continuation = continuation
        
        num_args = len(rest)
        self.num_bindings = num_args / 2
        if num_args == 0:
            return continuation.next(None)
        
        self.symbols = [""] * self.num_bindings
        self.unevaled = [None] * self.num_bindings
        self.evaled = [None] * self.num_bindings
        i = 0
        while i < num_args:
            arg = rest[i]
            if i % 2 == 0:
                if not isinstance(arg, Symbol):
                    raise EvalException("binding name is not a symbol")
                self.symbols[i / 2] = arg.name
            else:
                self.unevaled[i / 2] = arg
            i += 1
        
        return EvalState(scope, self.unevaled[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        self.evaled[i] = result
        if i + 1 >= self.num_bindings:
            # we're done
            j = 0
            ret = None
            while j < self.num_bindings:
                ret = self.evaled[j]
                self.scope.set(self.symbols[j], ret)
                j += 1
            return self.continuation.next(ret)
        
        # do the next one
        return EvalState(self.scope, self.unevaled[i + 1], CommonContinuation(self, i + 1))

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

@builtin_full('let')
class Let(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, rest = parse_arguments(args, 1, 0, True)
        
        self.scope = scope
        self.continuation = continuation
        self.body = rest
        
        if not isinstance(req[0], Cell):
            raise EvalException("let bindings are not a list")
        try:
            bindings = req[0].to_list()
        except InvalidValue:
            raise EvalException("let bindings are not a list")
        
        self.num_bindings = len(bindings)
        self.symbols = [""] * self.num_bindings
        self.unevaled = [None] * self.num_bindings
        self.evaled = [None] * self.num_bindings
        i = 0
        while i < self.num_bindings:
            binding = bindings[i]
            if isinstance(binding, Symbol):
                self.symbols[i] = binding.name
            elif isinstance(binding, Cell):
                try:
                    binding_list = binding.to_list()
                except InvalidValue:
                    raise EvalException("let binding is not a two-cell", binding)
                if len(binding_list) != 2:
                    raise EvalException("let binding is not a two-cell", binding)
                symbol = binding_list[0]
                expr = binding_list[1]
                if not isinstance(symbol, Symbol):
                    raise EvalException("let binding name is not a symbol", binding)
                self.symbols[i] = symbol.name
                self.unevaled[i] = expr
            else:
                raise EvalException("let binding is not a two-cell or a symbol", binding)
            i += 1
        
        # start the evaluation
        return EvalState(scope, self.unevaled[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        self.evaled[i] = result
        if i + 1 >= self.num_bindings:
            # we're done
            newscope = Scope(self.scope)
            j = 0
            while j < self.num_bindings:
                newscope.set(self.symbols[j], self.evaled[j], local_only=True)
                j += 1
            return EvalListState(newscope, self.body, self.continuation)
        
        # do the next one
        return EvalState(self.scope, self.unevaled[i + 1], CommonContinuation(self, i + 1))

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
