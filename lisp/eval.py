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

class EvalState(object):
    def __init__(self, scope, sexp, callback, callbackint):
        self.scope = scope
        self.sexp = sexp
        self.callback = callback
        self.callbackint = callbackint
    def next(self, result):
        return self.callback(self.callbackint, result)

class EvalLastState(EvalState):
    def __init__(self, scope, sexp):
        EvalState.__init__(self, scope, sexp, None, 0)
        self.result = None
    def next(self, result):
        self.result = result
        return None

class EvalFunctionHelper(object):
    def __init__(self, scope, func, args, continuation):
        self.scope = scope
        self.orig_func = func
        self.args = args
        self.continuation = continuation
        self.state = EvalState(scope, func, self.callback, 0)
    def callback(self, unused, func):
        if not isinstance(func, Procedure):
            raise EvalException("expression did not evaluate to procedure", self.orig_func)
        # call the function
        return func.call(self.scope, self.args, self.continuation)

def eval_intern(state):
    # FIXME jit
    while True:
        oldstate = state
        if isinstance(state.sexp, Cell):
            # evaluate a function
            helper = EvalFunctionHelper(state.scope, state.sexp.car, state.sexp.cdr, state)
            state = helper.state
        elif isinstance(state.sexp, Symbol):
            # symbol lookup
            try:
                val = state.scope.get(state.sexp.name)
            except NameNotSet:
                raise EvalException("symbol not set", state.sexp)
            state = state.next(val)
        else:
            # all other values are self-evaluating
            state = state.next(state.sexp)
        
        # if the new state is None, this means return altogether
        if state is None:
            assert isinstance(oldstate, EvalLastState)
            return oldstate.result

def eval(scope, sexp):
    return eval_intern(EvalLastState(scope, sexp))

class EvalListHelper(object):
    def __init__(self, scope, sexps):
        self.scope = scope
        self.sexps = sexps
        self.sexps_len = len(sexps)
        self.startstate = EvalState(scope, sexps[0], self.callback, 1)
    
    def callback(self, sexp_num, result):
        next_sexp = sexps[sexp_num]
        if sexp_num + 1 == self.sexps_len:
            # this is the last one, stop eval'ing
            return EvalLastState(self.scope, next_sexp)
        return EvalState(self.scope, next_sexp, self.callback, sexp_num + 1)

@unroll_safe
def eval_list(scope, sexps):
    sexps_len = len(sexps)
    if sexps_len == 0:
        return None
    elif sexps_len == 1:
        return eval(scope, sexps[0])
    else:
        # general case
        helper = EvalListHelper(scope, sexps)
        return eval_intern(helper.startstate)
