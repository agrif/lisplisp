from .procedure import procedure, parse_arguments
from ..types import BoxedType, Cell, Symbol, String, Number, Integer, Float, Procedure
from ..eval import EvalException, eval

import pypy.rlib.clibffi as ffi
from pypy.rpython.lltypesystem import rffi, lltype
from pypy.rlib.rdynload import DLOpenError

class FFIType(object):
    def __init__(self, name, type, lisp_type, to_ffi, call_to_lisp):
        self.name = name
        self.type = type
        if type == rffi.VOIDP:
            self.ffi_type = ffi.ffi_type_pointer
        else:
            self.ffi_type = ffi.cast_type_to_ffitype(type)
        self.lisp_type = lisp_type
        self.to_ffi = to_ffi
        self.call_to_lisp = call_to_lisp

typelist = [
    ('void', lltype.Void, None, None, None),
    ('int', rffi.INT, None, None, None),
    ('double', rffi.DOUBLE, Float, lambda v: v.value, lambda f: Float(f.call(rffi.DOUBLE))),
    ('char*', rffi.VOIDP, None, None, None),
]

symbol_to_type = {}
for el in typelist:
    symbol_to_type[el[0]] = FFIType(*el)

class FFIProcedure(Procedure):
    def __init__(self, lib, func, name, argtypes, restype):
        self.lib = lib
        self.ffi_func = func
        self.argtypes = argtypes
        self.restype = restype
        Procedure.__init__(self, lib.name + '::' + name)
    def call(self, scope, args):
        req, _, _ = parse_arguments(args, len(self.argtypes))

        if self.restype.call_to_lisp is None:
            raise NotImplementedError("unhandled type: " + self.restype.name)

        i = 0
        while i < len(self.argtypes):
            sexp = req[i]
            typ = self.argtypes[i]
            val = eval(scope, sexp)
            if typ.lisp_type is None or typ.to_ffi is None:
                self.ffi_func._clean_args()
                raise NotImplementedError("unhandled type: " + typ.name)
            if not isinstance(val, typ.lisp_type):
                self.ffi_func._clean_args()
                raise EvalException("argument is incorrect type", sexp)
            self.ffi_func.push_arg(typ.to_ffi(val))
            i += 1
        
        return self.restype.call_to_lisp(self.ffi_func)

class FFILibrary(BoxedType):
    def __init__(self, name):
        self.name = name
        self.lib = ffi.CDLL(name)
    def unparse(self):
        return "#<ffi-library #%s>" % (self.name,)
    
    def get_procedure(self, name, argtypes, restype):
        ffi_argtypes = []
        for typ in argtypes:
            ffi_argtypes.append(typ.ffi_type)
        func = self.lib.getpointer(name, ffi_argtypes, restype.ffi_type)
        return FFIProcedure(self, func, name, argtypes, restype)

@procedure('ffi-library')
def l_ffi_library(scope, args):
    req, _, _ = parse_arguments(args, 1)
    name = eval(scope, req[0])
    if not isinstance(name, String):
        raise EvalException("library name is not a string")
    try:
        return FFILibrary(name.data)
    except DLOpenError:
        raise EvalException("library could not be loaded")

@procedure('ffi-procedure')
def l_ffi_procedure(scope, args):
    req, opt, rest = parse_arguments(args, 2, 1, True)
    
    lib = eval(scope, req[0])
    if not isinstance(lib, FFILibrary):
        raise EvalException("first argument is not a library")
    
    name = eval(scope, req[1])
    if not isinstance(name, String):
        raise EvalException("procedure name is not a string")
    name = name.data
    
    if len(opt) > 0:
        restype = eval(scope, opt[0])
        if not isinstance(restype, Symbol):
            raise EvalException("result type is not a symbol")
        restype = restype.name
    else:
        restype = "void"
    
    argtypes = []
    for sexp in rest:
        typ = eval(scope, sexp)
        if not isinstance(typ, Symbol):
            raise EvalException("argument type is not a symbol", sexp)
        argtypes.append(typ.name)
    
    try:
        full_restype = symbol_to_type[restype]
    except KeyError:
        raise EvalException("unknown type: " + restype)
    full_argtypes = []
    for arg in argtypes:
        try:
            full_argtypes.append(symbol_to_type[arg])
        except KeyError:
            raise EvalException("unknown type: " + arg)
    
    return lib.get_procedure(name, full_argtypes, full_restype)

def register(scope):
    pass
