from .procedure import procedure, parse_arguments
from ..types import String, Symbol, Integer
from ..eval import EvalException, eval

import os

def symbol_to_num(sym):
    if sym == 'stdin':
        return 0
    elif sym == 'stdout':
        return 1
    elif sym == 'stderr':
        return 2
    return -1

@procedure('write')
def l_write(scope, args):
    req, _, _ = parse_arguments(args, 2)
    fd = eval(scope, req[0])
    if not isinstance(fd, Symbol):
        raise EvalException("unknown file")
    destfd = symbol_to_num(fd.name)
    if destfd == -1:
        raise EvalException("unknown file")
    
    s = eval(scope, req[1])
    if not isinstance(s, String):
        raise EvalException("data to write must be a string")
    
    written = os.write(destfd, s.data)
    return Integer(written)
