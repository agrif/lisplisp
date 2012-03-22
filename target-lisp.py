import sys
import os

from lisp.parser import parse
from lisp.scope import Scope
from lisp.builtins import register as register_builtins
from lisp.eval import eval_list, EvalException

def evaluate_file(scope, fname):
    fd = os.open(fname, os.O_RDONLY, 0777)
    data = ""
    while True:
        data_append = os.read(fd, 4096)
        if len(data_append) == 0:
            break
        data += data_append
    os.close(fd)
    
    parsed = parse(data)
    sexps = parsed.to_list()
    return eval_list(scope, sexps)

def entry_point(argv):
    try:
        filenames = argv[1:]
    except IndexError:
        print "You must supply a filename."
        return 1
    
    scope = Scope()
    register_builtins(scope)
    
    try:
        for i in range(len(filenames)):
            val = evaluate_file(scope, filenames[i])
            if val is None:
                print "nil"
            else:
                print val.unparse()
    except EvalException, e:
        e.pretty_print()
        return 1
    
    return 0

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def target(*args):
    return entry_point, None

if __name__ == "__main__":
    import sys
    sys.exit(entry_point(sys.argv))
