from .types import Cell, Symbol, Procedure
from .scope import NameNotSet

from pypy.rlib.jit import JitDriver, unroll_safe, hint

def get_location(i, sexps_len, sexps):
    j = 0
    ret = ""
    while j < sexps_len:
        sexp = sexps[j]
        if j == i:
            ret += "_"
        if sexp is None:
            ret += "nil"
        else:
            ret += sexp.unparse()
        if j == i:
            ret += "_"
        if j != sexps_len - 1:
            ret += " "
        j += 1
    return ret
jitdriver = JitDriver(greens=['i', 'sexps_len', 'sexps'], reds=['scope'], get_printable_location=get_location)

class EvalException(Exception):
    def __init__(self, message, sexp=None):
        self.message = message
        self.trace = []
        if sexp is not None:
            self.trace.append(sexp)
        #Exception.__init__(self, message)
    def propogate(self, sexp):
        self.trace.append(sexp)
        return self
    
    def pretty_print(self):
        print ""
        print "*** Exception:"
        print ""
        i = len(self.trace) - 1
        while i >= 0:
            sexp = self.trace[i]
            if sexp is None:
                print 'nil'
            else:
                print sexp.unparse()
            i -= 1
        print ""
        print "***", self.message

def eval(scope, sexp):
    if isinstance(sexp, Cell):
        try:
            function = eval(scope, sexp.car)
        except EvalException, e:
            raise e.propogate(sexp)
        args = sexp.cdr
        # call function with args
        if isinstance(function, Procedure):
            try:
                return function.call(scope, args)
            except EvalException, e:
                raise e.propogate(sexp)
            except Exception, e:
                raise
                #raise EvalException("An unknown error occurred.", sexp)
        # raise an eval exception
        e = EvalException("value does not evaluate to a procedure", function)
        raise e.propogate(sexp)
    elif isinstance(sexp, Symbol):
        try:
            return scope.get(sexp.name)
        except NameNotSet:
            raise EvalException("symbol is not set", sexp)
    
    # non-cells, non-symbols are atomic
    return sexp

@unroll_safe
def eval_list(scope, sexps):
    i = 0
    ret = None
    sexps_len = len(sexps)
    while i < sexps_len:
        jitdriver.jit_merge_point(sexps=sexps, sexps_len=sexps_len, scope=scope, i=i)
        sexp = hint(sexps[i], promote=True)
        ret = eval(scope, sexp)
        i += 1
    return ret

@unroll_safe
def eval_list_each(scope, sexps):
    i = 0
    ret = []
    while i < len(sexps):
        ret.append(eval(scope, sexps[i]))
        i += 1
    return ret
