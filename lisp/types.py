class LispType(object):
    def unparse(self):
        raise NotImplementedError("unparse")

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

_symbol_disallowed = "\".`',; \n\r\t()[]";

class Symbol(LispType):
    def __init__(self, name):
        for c in name:
            if c in _symbol_disallowed:
                raise InvalidValue("character not allowed in symbols: '%s'" % (c,))
        self.name = name
    def unparse(self):
        return self.name

class String(LispType):
    def __init__(self, data):
        self.data = data
    def unparse(self):
        return self.data

class Procedure(LispType):
    def __init__(self, name="f"):
        self.name = name
    def unparse(self):
        return "#<procedure #%s>" % (self.name,)
    def call(self, scope, args):
        raise NotImplementedError('call')
