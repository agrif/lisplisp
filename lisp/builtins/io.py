from .procedure import builtin, parse_arguments
from ..types import String, Symbol, Integer
from ..eval import EvalException

import os

def symbol_to_num(sym):
    if sym == 'stdin':
        return 0
    elif sym == 'stdout':
        return 1
    elif sym == 'stderr':
        return 2
    return -1

@builtin('write', 2)
def l_write(req, opt, rest):
    fd = req[0]
    if not isinstance(fd, Symbol):
        raise EvalException("unknown file")
    destfd = symbol_to_num(fd.name)
    if destfd == -1:
        raise EvalException("unknown file")
    
    s = req[1]
    if not isinstance(s, String):
        raise EvalException("data to write must be a string")
    
    written = os.write(destfd, s.data)
    return Integer(written)
