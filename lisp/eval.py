from .types import Cell, Symbol, Procedure
from .scope import NameNotSet

def eval(scope, sexp):
    if isinstance(sexp, Cell):
        function = eval(scope, sexp.car)
        args = sexp.cdr
        # call function with args
        if isinstance(function, Procedure):
            return function.call(scope, args)
        # raise an eval exception
        return None
    elif isinstance(sexp, Symbol):
        try:
            return scope.get(sexp.name)
        except NameNotSet:
            # raise an eval exception
            return None
    
    # non-cells, non-symbols are atomic
    return sexp
