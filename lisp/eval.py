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
    """An evaluation exception. This exception is used to implement
    exceptions in the interpreted program."""
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
    """Represents a continuation. Calling next(..) with a result
    should return a new evaluation state, containing both something to
    evaluate and another continuation."""
    def next(self, result):
        raise NotImplementedError("next")

class Continuable(object):
    """An object that can be used to implement a continuation. Pass
    this object and an integer into CommonContinuation to create a
    continuation that will call got_result(..) with that integer and
    the result given to next(..). got_result(..) should return an
    evaluation state."""
    def got_result(self, i, result):
        raise NotImplementedError("got_result")

class CommonContinuation(Continuation):
    """A Continuation implementation that uses a Continuable as a
    backend. This little dance is needed because closures don't really
    work very well with RPython."""
    def __init__(self, continuable, i):
        self.continuable = continuable
        self.i = i
    def next(self, result):
        return self.continuable.got_result(self.i, result)

class EvalState(Continuation):
    """An evaluation state. This is a storage object for a scope, an
    expression to evaluate in that scope, and a continuation to call
    when that expression is done evaluating. Use this to evaluate
    sub-expressions without recursively calling eval(..)."""
    def __init__(self, scope, sexp, continuation):
        self.scope = scope
        self.sexp = sexp
        self.continuation = continuation
    def next(self, result):
        if self.continuation is not None:
            return self.continuation.next(result)

class EvalEndState(EvalState):
    """A special evaluation state that indicates the eval(..) function
    should return with the value given to next(..). This is used
    internally and you probably shouldn't use it outside of
    eval.py."""
    def __init__(self):
        EvalState.__init__(self, None, None, None)
        self.result = None
    def next(self, result):
        if self.result is None:
            self.result = result
        return self

class EvalFunctionState(EvalState):
    """A special evaluation state for evaluating a symbol into a
    function, then calling that function with the given arguments and
    continuation. This is used internally and probably shouldn't be
    used outside of eval.py."""
    def __init__(self, scope, func, args, continuation):
        EvalState.__init__(self, scope, func, continuation)
        self.args = args
    def next(self, result):
        if not isinstance(result, Procedure):
            raise EvalException("expression did not evaluate to a procedure", self.sexp)
        return result.call(self.scope, self.args, self.continuation)

class EvalListState(EvalState):
    """A useful evaluation state for evaluating a list of
    expressions. The result of the final expression is provided to the
    given continuation."""
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
def _eval_intern(state):
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
    """Evaluate a list of expressions in the given scope. As with all
    evaluation functions, this should *not* be called recursively for
    continuations to work properly."""
    return _eval_intern(EvalListState(scope, sexps, EvalEndState()))

def eval(scope, sexp):
    """Evaluate an expression in the given scope. As with all
    evaluation functions, this should *not* be called recursively for
    continuations to work properly."""
    return _eval_intern(EvalState(scope, sexp, EvalEndState()))
