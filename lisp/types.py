class LispType(object):
    def unparse(self):
        raise NotImplementedError("unparse")
    def eq(self, other):
        raise NotImplementedError("eq")

class BoxedType(LispType):
    def eq(self, other):
        if not isinstance(other, BoxedType):
            return False
        return (self is other)

class InvalidValue(Exception):
    pass

class Cell(LispType):
    def __init__(self, car, cdr=None):
        self.car = car
        self.cdr = cdr
    def _unparse_internal(self):
        gather = ""
        if self.car is None:
            gather += "nil"
        else:
            gather += self.car.unparse()
        if self.cdr is not None:
            if isinstance(self.cdr, Cell):
                gather += ' ' + self.cdr._unparse_internal()
            else:
                gather += ' . ' + self.cdr.unparse()
        return gather
    def unparse(self):
        return "(" + self._unparse_internal() + ")"
    def eq(self, other):
        if not isinstance(other, Cell):
            return False
        if self.car is None and other.car is None:
            return True
        if self.car is not None and self.car.eq(other.car):
            return True
        if self.cdr is None and other.cdr is None:
            return True
        if self.cdr is not None and self.cdr.eq(other.cdr):
            return True
        return False
    def to_list(self):
        ret = []
        sexp = self
        while sexp is not None:
            if not isinstance(sexp, Cell):
                raise InvalidValue("cell is not a list")
            ret.append(sexp.car)
            sexp = sexp.cdr
        return ret

class Number(LispType):
    def get_float(self):
        raise NotImplementedError('get_float')

class Integer(Number):
    def __init__(self, val):
        self.value = val
    def get_float(self):
        return float(self.value)
    def unparse(self):
        return str(self.value)
    def eq(self, other):
        if not isinstance(other, Integer):
            return False
        return self.value == other.value

class Float(Number):
    def __init__(self, val):
        self.value = val
    def get_float(self):
        return self.value
    def unparse(self):
        return str(self.value)
    def eq(self, other):
        if not isinstance(other, Float):
            return False
        return self.value == other.value

_symbol_disallowed = "\".`',; \n\r\t()[]";

class Symbol(LispType):
    def __init__(self, name):
        for c in name:
            if c in _symbol_disallowed:
                raise InvalidValue("character not allowed in symbols: '%s'" % (c,))
        self.name = name
    def unparse(self):
        return self.name
    def eq(self, other):
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name

class String(LispType):
    def __init__(self, data):
        self.data = data
    def unparse(self):
        return self.data
    def eq(self, other):
        if not isinstance(other, String):
            return False
        return self.data == other.data

class Procedure(LispType):
    def __init__(self, name="f"):
        self.name = name
    def unparse(self):
        return "#<procedure #%s>" % (self.name,)
    def call(self, scope, args):
        raise NotImplementedError('call')
    def eq(self, other):
        if not isinstance(other, Procedure):
            return False
        return (self is other)
