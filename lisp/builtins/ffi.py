from .procedure import builtin, parse_arguments, GenericContinuable
from ..types import BoxedType, Cell, Symbol, String, Number, Integer, Float, Procedure
from ..eval import EvalException

import pypy.rlib.clibffi as ffi
from pypy.rpython.lltypesystem import rffi, lltype
from pypy.rlib.rdynload import DLOpenError

c_free = rffi.llexternal("free", [rffi.VOIDP], lltype.Void)

class FFIType(object):
    name = "void"
    type = lltype.Void
    ffi_type = ffi.ffi_type_void
    lisp_type = None
    
    def check_lisp_type(self, obj):
        if not isinstance(obj, self.lisp_type):
            return False
        return True
    
    def push_arg(self, func, val):
        #func.push_arg(val)
        raise NotImplementedError("push_arg")
    def free_arg(self):
        pass
    def call(self, func):
        func.call(lltype.Void)
        return None
    
class IntType(FFIType):
    name = 'int'
    type = rffi.INT
    ffi_type = ffi.ffi_type_sint
    lisp_type = Integer
    def push_arg(self, func, val):
        assert isinstance(val, Integer)
        func.push_arg(val.value)
    def call(self, func):
        return Integer(int(func.call(rffi.INT)))
class DoubleType(FFIType):
    name = 'double'
    type = rffi.DOUBLE
    ffi_type = ffi.ffi_type_double
    lisp_type = Float
    def push_arg(self, func, val):
        assert isinstance(val, Float)
        func.push_arg(val.value)
    def call(self, func):
        return Float(float(func.call(rffi.DOUBLE)))
class StringType(FFIType):
    name = 'char*'
    type = rffi.CCHARP
    ffi_type = ffi.ffi_type_pointer
    lisp_type = String
    def check_lisp_type(self, obj):
        if obj is None:
            return True
        if not isinstance(obj, String):
            return False
        return True
    def push_arg(self, func, val):
        if val is None:
            # nil -> NULL
            self.charp = lltype.nullptr(rffi.CCHARP.TO)
        else:
            assert isinstance(val, String)
            self.charp = rffi.str2charp(val.data)
        func.push_arg(self.charp)
    def free_arg(self):
        if self.charp:
            lltype.free(self.charp, flavor='raw')
    def call(self, func):
        charp = func.call(rffi.CCHARP)
        if not charp:
            return None # NULL -> nil
        ret = String(rffi.charp2str(charp))
        c_free(charp)
        return ret

typelist = [
    FFIType,
    IntType,
    DoubleType,
    StringType,
]

symbol_to_type = {}
for el in typelist:
    symbol_to_type[el.name] = el

class FFIContinuable(GenericContinuable):
    def __init__(self, argtypes, restype, ffi_func):
        GenericContinuable.__init__(self, len(argtypes), 0, False, True, False, False)
        self.argtypes = argtypes
        self.restype = restype
        self.ffi_func = ffi_func
    def call_backend(self, req, opt, rest):
        i = 0
        to_free = []
        while i < len(self.argtypes):
            val = req[i]
            typ = self.argtypes[i]()
            if not typ.check_lisp_type(val):
                self.ffi_func._clean_args()
                for free_obj in to_free:
                    free_obj.free_arg()
                raise EvalException("argument is incorrect type")
            typ.push_arg(self.ffi_func, val)
            to_free.append(typ)
            i += 1
        
        ret = self.restype().call(self.ffi_func)
        for free_obj in to_free:
            free_obj.free_arg()
        return ret

class FFIProcedure(Procedure):
    def __init__(self, lib, func, name, argtypes, restype):
        self.lib = lib
        self.ffi_func = func
        self.argtypes = argtypes
        self.restype = restype
        Procedure.__init__(self, lib.name + '::' + name)
    def call(self, scope, args, continuation):
        obj = FFIContinuable(self.argtypes, self.restype, self.ffi_func)
        return obj.call(scope, args, continuation)

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

@builtin('ffi-library', 1)
def l_ffi_library(req, opt, rest):
    name = req[0]
    if not isinstance(name, String):
        raise EvalException("library name is not a string")
    try:
        return FFILibrary(name.data)
    except DLOpenError:
        raise EvalException("library could not be loaded")

@builtin('ffi-procedure', 2, 1, True)
def l_ffi_procedure(req, opt, rest):
    lib = req[0]
    if not isinstance(lib, FFILibrary):
        raise EvalException("first argument is not a library")
    
    name = req[1]
    if not isinstance(name, String):
        raise EvalException("procedure name is not a string")
    name = name.data
    
    if len(opt) > 0:
        restype = opt[0]
        if not isinstance(restype, Symbol):
            raise EvalException("result type is not a symbol")
        restype = restype.name
    else:
        restype = "void"
    
    argtypes = []
    for typ in rest:
        if not isinstance(typ, Symbol):
            raise EvalException("argument type is not a symbol")
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
