from ..types import Procedure, Cell
from ..eval import EvalException

procedures = []

class AutoProcedure(Procedure):
    def __init__(self, name, func):
        self.func = func
        self.name = name
        Procedure.__init__(self, name)
    def call(self, scope, args):
        return self.func(scope, args)

def procedure(name):
    def register(func):
        proc = AutoProcedure(name, func)
        procedures.append(proc)
    return register

def register(scope):
    for proc in procedures:
        scope.set(proc.name, proc)

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
