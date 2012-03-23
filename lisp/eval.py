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

class Continuation(object):
    def next(self, result):
        raise NotImplementedError("next")

class Continuable(object):
    def got_result(self, i, result):
        raise NotImplementedError("got_result")

class CommonContinuation(Continuation):
    def __init__(self, continuable, i):
        self.continuable = continuable
        self.i = i
    def next(self, result):
        return self.continuable.got_result(self.i, result)

class EvalState(Continuation):
    def __init__(self, scope, sexp, continuation):
        self.scope = scope
        self.sexp = sexp
        self.continuation = continuation
    def next(self, result):
        if self.continuation is not None:
            return self.continuation.next(result)

class EvalEndState(EvalState):
    def __init__(self):
        EvalState.__init__(self, None, None, None)
        self.result = None
    def next(self, result):
        if self.result is None:
            self.result = result
        return self

class EvalFunctionState(EvalState):
    def __init__(self, scope, func, args, continuation):
        EvalState.__init__(self, scope, func, continuation)
        self.args = args
    def next(self, result):
        if not isinstance(result, Procedure):
            raise EvalException("expression did not evaluate to a procedure", self.sexp)
        return result.call(self.scope, self.args, self.continuation)

class EvalListState(EvalState):
    def __init__(self, scope, sexps, continuation):
        EvalState.__init__(self, scope, None, continuation)
        self.sexps = sexps
        self.sexps_len = len(sexps)
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
        if sexp is None:
            print "# evaluating nil"
        else:
            print "# evaluating", sexp.unparse()
        
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
