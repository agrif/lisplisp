from ..types import InvalidValue, Procedure, Cell, Symbol
from ..eval import EvalException, Continuable, CommonContinuation, EvalState, EvalListState
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

class GenericContinuable(Continuable):
    """A generic continuable that evaluates (or doesn't) all
    arguments, calls a backend function at self.call_backend, and then
    evaluates (or doesn't) the result. If you set extra to True, call_backend_extra is called instead, which should return an eval state."""
    def __init__(self, req, opt, rest, eval_args, eval_return, extra):
        self.num_req = req
        self.num_opt = opt
        self.use_rest = rest
        self.eval_args = eval_args
        self.eval_return = eval_return
        self.use_extra = extra
    def call_backend(self, req, opt, rest):
        raise NotImplementedError("call_backend")
    def call_backend_extra(self, req, opt, rest, continuation):
        raise NotImplementedError("call_backend_extra")
    def _call_helper(self, req, opt, rest):
        if self.use_extra:
            if self.eval_return:
                subcont = CommonContinuation(self, self.total_args)
            else:
                subcont = self.continuation
            return self.call_backend_extra(req, opt, rest, subcont)
        else:
            if self.eval_return:
                return EvalState(self.scope, self.call_backend(req, opt, rest), self.continuation)
            else:
                return self.continuation.next(self.call_backend(req, opt, rest))
    
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
        
        if self.total_args == 0 or not self.eval_args:
            # there are no arguments, or they don't need eval'd,
            # skip to the end
            return self._call_helper(req, opt, rest)
        
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
        # handle the extra return value case
        if i == self.total_args:
            assert self.eval_return
            return EvalState(self.scope, result, self.continuation)
        
        # everything after this is evaluating an argument
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
            return self._call_helper(self.req, self.opt, self.rest)
        
        # get the next thing to evaluate
        if i < self.num_req:
            next = self.req_uneval[i]
        elif i < self.num_req + self.avail_opt:
            next = self.opt_uneval[i - self.num_req]
        else:
            assert i < self.total_args
            next = self.rest_uneval[i - self.num_req - self.avail_opt]
        return EvalState(self.scope, next, CommonContinuation(self, i))

class BuiltinSimple(GenericContinuable):
    """Similar to BuiltinFull but used internally for simple builtins
    that have no special evaluation rules. Evaluates all arguments,
    then returns the result unevaled."""
    def __init__(self, func, req, opt, rest):
        GenericContinuable.__init__(self, req, opt, rest, True, False, False)
        self.func = func
    def call_backend(self, req, opt, rest):
        return self.func(req, opt, rest)

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

class LambdaContinuable(GenericContinuable):
    """Similar to BuiltinFull but used internally for simple builtins
    that have no special evaluation rules. Evaluates all arguments,
    then returns the result unevaled."""
    def __init__(self, scope, body, req_names, opt_names, rest_name, eval_args, eval_return):
        GenericContinuable.__init__(self, len(req_names), len(opt_names), rest_name is not None, eval_args, eval_return, True)
        self.scope = scope
        self.body = body
        self.req_names = req_names
        self.opt_names = opt_names
        self.rest_name = rest_name
    def call_backend_extra(self, req, opt, rest, continuation):
        num_req = len(req)
        num_opt = len(opt)
        num_opt_max = len(self.opt_names)
        assert len(self.req_names) == num_req
        assert num_opt_max >= num_opt
        newscope = Scope(self.scope)
        
        i = 0
        while i < num_req:
            newscope.set(self.req_names[i], req[i])
            i += 1
        i = 0
        while i < num_opt:
            newscope.set(self.opt_names[i], opt[i])
            i += 1
        while i < num_opt_max:
            newscope.set(self.opt_names[i], None)
            i += 1
        if self.rest_name is not None:
            rest_dup = list(rest)
            rest_dup.reverse()
            rest_lisp = None
            for sexp in rest_dup:
                rest_lisp = Cell(sexp, rest_lisp)
            newscope.set(self.rest_name, rest_lisp)
        
        return EvalListState(newscope, self.body, continuation)

class LambdaProcedure(Procedure):
    def __init__(self, scope, body, req_names, opt_names, rest_name, eval_args, eval_return, name):
        Procedure.__init__(self, name)
        self.scope = scope
        self.body = body
        self.req_names = req_names
        self.opt_names = opt_names
        self.rest_name = rest_name
        self.eval_args = eval_args
        self.eval_return = eval_return
    def call(self, scope, args, continuation):
        obj = LambdaContinuable(self.scope, self.body, self.req_names, self.opt_names, self.rest_name, self.eval_args, self.eval_return)
        return obj.call(scope, args, continuation)

@unroll_safe
def _l_lambda_macro(scope, args, eval_args, eval_return):
    req, _, rest = parse_arguments(args, 1, 0, True)
    if not isinstance(req[0], Cell):
        raise EvalException("not a valid argument list")
    try:
        argnames = req[0].to_list()
    except InvalidValue:
        raise EvalException("not a valid argument list")
    
    phase = 0
    required = []
    optional = []
    restname = None
    
    for sexp in argnames:
        if not isinstance(sexp, Symbol):
            raise EvalException("not a valid binding name", sexp)
        name = sexp.name
        
        if name == "&optional":
            if phase == 1:
                raise EvalException("&optional may only appear once")
            if phase == 2:
                raise EvalException("&optional must appear before &rest")
            phase = 1
            continue
        elif name == "&rest":
            if phase == 2:
                raise EvalException("&rest may only appear once")
            phase = 2
            continue
        
        if phase == 3 and restname is not None:
            raise EvalException("there may be only one &rest binding")
        
        if phase == 0:
            required.append(name)
        elif phase == 1:
            optional.append(name)
        else:
            restname = name
    
    return LambdaProcedure(scope, rest, required, optional, restname, eval_args, eval_return, "unknown")

@builtin_full('lambda')
class Lambda(BuiltinFull):
    def call(self, scope, args, continuation):
        proc = _l_lambda_macro(scope, args, True, False)
        return continuation.next(proc)

@builtin_full('macro')
class Lambda(BuiltinFull):
    def call(self, scope, args, continuation):
        proc = _l_lambda_macro(scope, args, False, True)
        return continuation.next(proc)

class LispContinuation(Procedure):
    def __init__(self, continuation):
        Procedure.__init__(self, "continuation")
        self.wrapped_continuation = continuation
    def call(self, scope, args, continuation):
        req, _, _ = parse_arguments(args, 1)
        # evaluate the return value, then use our continuation
        return EvalState(scope, req[0], self.wrapped_continuation)

@builtin_full('call/cc')
class CallCC(BuiltinFull):
    def call(self, scope, args, continuation):
        req, _, _ = parse_arguments(args, 1)        
        self.scope = scope
        self.continuation = continuation
        # eval the argument to get a procedure
        return EvalState(scope, req[0], CommonContinuation(self, 0))
    def got_result(self, i, result):
        if not isinstance(result, Procedure):
            raise EvalException("provided value is not a procedure")
        curcont = LispContinuation(self.continuation)
        return result.call(self.scope, Cell(curcont), self.continuation)
