class LispType(object):
    def get_type(self):
        raise NotImplementedError("get_type")
    def unparse(self):
        raise NotImplementedError("unparse")

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

class Symbol(LispType):
    def __init__(self, name):
        self.name = name
    def unparse(self):
        return self.name
