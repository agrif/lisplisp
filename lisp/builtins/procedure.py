from ..types import InvalidValue, Procedure, Cell, Symbol
from ..eval import EvalException, eval, eval_list

from pypy.rlib.jit import unroll_safe, hint

procedures = []

class AutoProcedure(Procedure):
    _immutable_fields_ = ['func']
    def __init__(self, name, func):
        self.func = func
        self.name = name
        Procedure.__init__(self, name)
    def call(self, scope, args):
        self = hint(self, promote=True)
        return self.func(scope, args)

def procedure(name):
    def register(func):
        proc = AutoProcedure(name, func)
        procedures.append(proc)
        return func
    return register

def register(scope):
    for proc in procedures:
        scope.set(proc.name, proc)

@unroll_safe
def parse_arguments(args, num_required, num_optional=0, use_rest=False):
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

class LambdaProcedure(Procedure):
    _immutable_fields_ = ['required', 'optional', 'rest', 'body', 'eval_args', 'eval_return']
    def __init__(self, required, optional, rest, body, eval_args=True, eval_return=False):
        self.required = required
        self.optional = optional
        self.rest = rest
        self.body = body
        
        self.eval_args = eval_args
        self.eval_return = eval_return
        
        Procedure.__init__(self, 'nil')
    
    @unroll_safe
    def call(self, scope, args):
        self = hint(self, promote=True)
        
        reqvals, optvals, restvals = parse_arguments(args, len(self.required), len(self.optional), self.rest is not None)
        restvals.reverse()
        newscope = {}
        
        for i in range(len(self.required)):
            if self.eval_args:
                tmp = eval(scope, reqvals[i])
            else:
                tmp = reqvals[i]
            newscope[self.required[i]] = tmp
        for i in range(len(self.optional)):
            if i < len(optvals):
                if self.eval_args:
                    tmp = eval(scope, optvals[i])
                else:
                    tmp = optvals[i]
                newscope[self.optional[i]] = tmp
            else:
                newscope[self.optional[i]] = None
        rest_cell = None
        for sexp in restvals:
            if self.eval_args:
                tmp = eval(scope, sexp)
            else:
                tmp = sexp
            rest_cell = Cell(tmp, rest_cell)
        if self.rest is not None:
            newscope[self.rest] = rest_cell
        
        scope.push()
        try:
            for name, value in newscope.items():
                scope.set(name, value)
            ret = eval_list(scope, self.body)
        finally:
            scope.pop()
        
        if self.eval_return:
            return eval(scope, ret)
        return ret

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
        
    return LambdaProcedure(required, optional, restname, rest, eval_args, eval_return)

@procedure('lambda')
def l_lambda(scope, args):
    return _l_lambda_macro(scope, args, True, False)

@procedure('macro')
def l_lambda(scope, args):
    return _l_lambda_macro(scope, args, False, True)
