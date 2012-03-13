from .types import Cell, Symbol, Procedure
from .scope import NameNotSet

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
        function = eval(scope, sexp.car)
        args = sexp.cdr
        # call function with args
        if isinstance(function, Procedure):
            try:
                return function.call(scope, args)
            except EvalException, e:
                raise e.propogate(sexp)
            except Exception, e:
                raise EvalException("An unknown error occurred.", sexp)
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
