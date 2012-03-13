class NameNotSet(Exception):
    pass
class EmptyStack(Exception):
    pass

class Scope(object):
    def __init__(self):
        self.stack = []
        self.current = {}

    def push(self):
        self.stack.push(self.current)
        self.current = self.current.copy()
    def pop(self):
        try:
            self.current = self.stack.pop()
        except IndexError:
            raise EmptyStack("no scopes left to pop")
    
    def set(self, name, val):
        self.current[name] = val
    def get(self, name):
        try:
            return self.current[name]
        except KeyError:
            raise NameNotSet(name)
