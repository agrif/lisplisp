import sys
import os

from lisp.parser import parse

def entry_point(argv):
    try:
        filename = argv[1]
    except IndexError:
        print "You must supply a filename."
        return 1
    
    fd = os.open(filename, os.O_RDONLY, 0777)
    data = ""
    while True:
        data_append = os.read(fd, 4096)
        if len(data_append) == 0:
            break
        data += data_append
    os.close(fd)
    
    sexp = parse(data)
    while sexp:
        if sexp.car is None:
            print "nil"
        else:
            print sexp.car.unparse()
        sexp = sexp.cdr
    return 0

def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def target(*args):
    return entry_point, None

if __name__ == "__main__":
    import sys
    sys.exit(entry_point(sys.argv))
