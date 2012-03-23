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

class EvalStateBase(object):
    def __init__(self, scope, sexp):
        self.scope = scope
        self.sexp = sexp
    def next(self, result):
        raise NotImplementedError("base")

class EvalState(EvalStateBase):
    def __init__(self, scope, sexp, callbackobj, callbackint):
        EvalStateBase.__init__(self, scope, sexp)
        self.callbackobj = callbackobj
        self.callbackint = callbackint
    def next(self, result):
        if self.callbackobj is not None:
            return self.callbackobj.got_result(self.callbackint, result)
        return None

class EvalEndState(EvalStateBase):
    def __init__(self):
        EvalStateBase.__init__(self, None, None)
        self.result = None
    def next(self, result):
        if self.result is None:
            self.result = result
        return self

class EvalFunctionState(EvalStateBase):
    def __init__(self, scope, func, args, continuation):
        EvalStateBase.__init__(self, scope, func)
        self.args = args
        self.continuation = continuation
    def next(self, result):
        if not isinstance(result, Procedure):
            raise EvalException("expression did not evaluate to a procedure", self.sexp)
        return result.call(self.scope, self.args, self.continuation)

class EvalListState(EvalStateBase):
    def __init__(self, scope, sexps, continuation):
        EvalStateBase.__init__(self, scope, None)
        self.sexps = sexps
        self.sexps_len = len(sexps)
        self.continuation = continuation        
        self.current = 0
        if self.sexps_len > 0:
            self.sexp = sexps[0]
        else:
            self.sexp = None
    def next(self, result):
        if not self.current + 1 < self.sexps_len:
            # this is the last one
            return self.continuation.next(result)
        
        # move on to the next sexp
        self.current += 1
        self.sexp = self.sexps[self.current]
        return self

@unroll_safe
def eval_intern(state):
    # FIXME jit
    while True:
        # if this is an end state, return
        if isinstance(state, EvalEndState):
            return state.result
        
        sexp = state.sexp
        # evaluate the sexp
        if isinstance(sexp, Cell):
            # evaluate a function
            state = EvalFunctionState(state.scope, sexp.car, sexp.cdr, state)
        elif isinstance(sexp, Symbol):
            # symbol lookup
            try:
                val = state.scope.get(sexp.name)
            except NameNotSet:
                raise EvalException("symbol not set", sexp)
            state = state.next(val)
        else:
            # all other values are self-evaluating
            state = state.next(sexp)

def eval_list(scope, sexps):
    return eval_intern(EvalListState(scope, sexps, EvalEndState()))

def eval(scope, sexp):
    return eval_list(scope, [sexp])
