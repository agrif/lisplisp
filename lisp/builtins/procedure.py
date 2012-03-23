from ..types import InvalidValue, Procedure, Cell, Symbol
from ..eval import EvalException, Continuable, CommonContinuation, EvalState
from ..scope import Scope

from pypy.rlib.jit import unroll_safe, hint

class BuiltinFull(Continuable):
    """A Continuable used for builtin functions that need special
    handling. Note that in order for continuations to work everywhere,
    you *must* accept calls to got_result that it has already
    recieved. Continuations may cause the evaluator to backtrack.
    
    Decorate subclasses with @builtin_full(name) to automatically
    create a procedure wrapping it and register it automatically in
    new scopes."""
    def call(self, scope, args, continuation):
        raise NotImplementedError('call')

class BuiltinFullProcedure(Procedure):
    def __init__(self, cls, name):
        Procedure.__init__(self, name)
        self.backend = cls
    def call(self, scope, args, continuation):
        obj = self.backend()
        return obj.call(scope, args, continuation)

class BuiltinSimple(Continuable):
    """Similar to BuiltinFull but used internally for simple builtins
    that have no special evaluation rules."""
    def __init__(self, func, req, opt, rest):
        self.num_req = req
        self.num_opt = opt
        self.use_rest = rest
        self.func = func
    def call(self, scope, args, continuation):
        req, opt, rest = parse_arguments(args, self.num_req, self.num_opt, self.use_rest)
        self.avail_opt = len(opt)
        self.avail_rest = len(rest)
        self.total_args = self.num_req + self.avail_opt + self.avail_rest
        self.req_uneval = req
        self.opt_uneval = opt
        self.rest_uneval = rest
        self.scope = scope
        self.continuation = continuation
        
        if self.total_args == 0:
            # there are no arguments, skip to the end
            return continuation.next(self.func(req, opt, rest))
        
        # set up eval'd destinations
        self.req = [None] * self.num_req
        self.opt = [None] * self.avail_opt
        self.rest = [None] * self.avail_rest
        
        # find the first argument
        if self.num_req > 0:
            first = req[0]
        elif self.avail_opt > 0:
            first = opt[0]
        else:
            first = rest[0]
        return EvalState(scope, first, CommonContinuation(self, 0))
    def got_result(self, i, result):
        # store the result
        if i < self.num_req:
            self.req[i] = result
        elif i < self.num_req + self.avail_opt:
            self.opt[i - self.num_req] = result
        else:
            assert i < self.total_args
            self.rest[i - self.num_req - self.avail_opt] = result
        
        # increment i, check to see if done
        i += 1
        if i >= self.total_args:
            return self.continuation.next(self.func(self.req, self.opt, self.rest))
        
        # get the next thing to evaluate
        if i < self.num_req:
            next = self.req[i]
        elif i < self.num_req + self.avail_opt:
            next = self.opt[i - self.num_req]
        else:
            assert i < self.total_args
            next = self.rest[i - self.num_req - self.avail_opt]
        return EvalState(self.scope, next, CommonContinuation(self, i))

class BuiltinSimpleProcedure(Procedure):
    def __init__(self, func, req, opt, rest, name):
        Procedure.__init__(self, name)
        self.func = func
        self.req = req
        self.opt = opt
        self.rest = rest
    def call(self, scope, args, continuation):
        obj = BuiltinSimple(self.func, self.req, self.opt, self.rest)
        return obj.call(scope, args, continuation)

procedures = []

def builtin_full(name):
    def builtin_full_intern(cls):
        procedures.append(BuiltinFullProcedure(cls, name))
        return cls
    return builtin_full_intern

def builtin(name, req=0, opt=0, rest=False):
    def builtin_intern(func):
        proc = BuiltinSimpleProcedure(func, req, opt, rest, name)
        procedures.append(proc)
        return func
    return builtin_intern

def register(scope):
    for proc in procedures:
        scope.set_semiconstant(proc.name, proc)

@unroll_safe
def parse_arguments(args, num_required=0, num_optional=0, use_rest=False):
    required = []
    optional = []
    rest = []
    
    if use_rest:
        errorstr = "invalid number of arguments: takes at least " + str(num_required)
    else:
        if num_optional > 0:
            errorstr = "invalid number of arguments: takes between " + str(num_required) + " and " + str(num_required + num_optional)
        else:
            errorstr = "invalid number of arguments: takes exactly " + str(num_required)
    
    for _ in xrange(num_required):
        if args is None:
            raise EvalException(errorstr)
        if not isinstance(args, Cell):
            raise EvalException("not a valid argument list")
        required.append(args.car)
        args = args.cdr
    
    for _ in xrange(num_optional):
        if args is None:
            break
        if not isinstance(args, Cell):
            raise EvalException("not a valid argument list")
        optional.append(args.car)
        args = args.cdr
    
    while use_rest and (args is not None):
        if not isinstance(args, Cell):
            raise EvalException("not a valid argument list")
        rest.append(args.car)
        args = args.cdr
    
    if args is not None:
        if not isinstance(args, Cell):
            raise EvalException("not a valid argument list")
        raise EvalException(errorstr)
    
    return (required, optional, rest)

# class LambdaProcedure(Procedure):
#     _immutable_fields_ = ['required', 'optional', 'rest', 'body', 'eval_args', 'eval_return']
#     def __init__(self, scope, required, optional, rest, body, eval_args=True, eval_return=False):
#         self.scope = scope
#         self.required = required
#         self.optional = optional
#         self.rest = rest
#         self.body = body
        
#         self.eval_args = eval_args
#         self.eval_return = eval_return
        
#         Procedure.__init__(self, 'nil')
    
#     @unroll_safe
#     def call(self, scope, args):
#         self = hint(self, promote=True)
        
#         reqvals, optvals, restvals = parse_arguments(args, len(self.required), len(self.optional), self.rest is not None)
#         restvals.reverse()
#         newscope = {}
        
#         for i in range(len(self.required)):
#             if self.eval_args:
#                 tmp = eval(scope, reqvals[i])
#             else:
#                 tmp = reqvals[i]
#             newscope[self.required[i]] = tmp
#         for i in range(len(self.optional)):
#             if i < len(optvals):
#                 if self.eval_args:
#                     tmp = eval(scope, optvals[i])
#                 else:
#                     tmp = optvals[i]
#                 newscope[self.optional[i]] = tmp
#             else:
#                 newscope[self.optional[i]] = None
#         rest_cell = None
#         for sexp in restvals:
#             if self.eval_args:
#                 tmp = eval(scope, sexp)
#             else:
#                 tmp = sexp
#             rest_cell = Cell(tmp, rest_cell)
#         if self.rest is not None:
#             newscope[self.rest] = rest_cell
        
#         newscope_obj = Scope(self.scope)
#         for name, value in newscope.items():
#             newscope_obj.set_semiconstant(name, value, local_only=True)
#         ret = eval_list(newscope_obj, self.body)
        
#         if self.eval_return:
#             return eval(scope, ret)
#         return ret

# @unroll_safe
# def _l_lambda_macro(scope, args, eval_args, eval_return):
#     req, _, rest = parse_arguments(args, 1, 0, True)
#     if not isinstance(req[0], Cell):
#         raise EvalException("not a valid argument list")
#     try:
#         argnames = req[0].to_list()
#     except InvalidValue:
#         raise EvalException("not a valid argument list")
    
#     phase = 0
#     required = []
#     optional = []
#     restname = None
    
#     for sexp in argnames:
#         if not isinstance(sexp, Symbol):
#             raise EvalException("not a valid binding name", sexp)
#         name = sexp.name
        
#         if name == "&optional":
#             if phase == 1:
#                 raise EvalException("&optional may only appear once")
#             if phase == 2:
#                 raise EvalException("&optional must appear before &rest")
#             phase = 1
#             continue
#         elif name == "&rest":
#             if phase == 2:
#                 raise EvalException("&rest may only appear once")
#             phase = 2
#             continue
        
#         if phase == 3 and restname is not None:
#             raise EvalException("there may be only one &rest binding")
        
#         if phase == 0:
#             required.append(name)
#         elif phase == 1:
#             optional.append(name)
#         else:
#             restname = name
        
#     return LambdaProcedure(scope, required, optional, restname, rest, eval_args, eval_return)

# @procedure('lambda')
# def l_lambda(scope, args):
#     return _l_lambda_macro(scope, args, True, False)

# @procedure('macro')
# def l_lambda(scope, args):
#     return _l_lambda_macro(scope, args, False, True)
