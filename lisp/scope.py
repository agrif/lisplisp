from pypy.rlib.jit import hint, elidable as purefunction

class NameNotSet(Exception):
    pass
class EmptyStack(Exception):
    pass

class VersionTag(object):
    pass

class Scope(object):
    def __init__(self):
        self.stack = []
        self.current = {}
        
        self.semiconstant_version = VersionTag()
        self.semiconstants = []

    def push(self):
        self.stack.append(self.current)
        self.current = self.current.copy()
    def pop(self):
        try:
            self.current = self.stack.pop()
        except IndexError:
            raise EmptyStack("no scopes left to pop")
    
    @purefunction
    def _is_semiconstant(self, name, version):
        return (name in self.semiconstants)
    
    def _set_intern(self, name, val):
        self.current[name] = val
    def set_semiconstant(self, name, val):
        self = hint(self, promote=True)
        sc_version = hint(self.semiconstant_version, promote=True)
        
        self._set_intern(name, val)
        if not self._is_semiconstant(name, sc_version):
            self.semiconstants.append(name)
        self.semiconstant_version = VersionTag()
    def set(self, name, val):
        self = hint(self, promote=True)
        sc_version = hint(self.semiconstant_version, promote=True)
        
        if self._is_semiconstant(name, sc_version):
            self.set_semiconstant(name, val)
        else:
            self._set_intern(name, val)

    def _get_intern(self, name):
        try:
            return self.current[name]
        except KeyError:
            raise NameNotSet(name)
    @purefunction
    def _get_semiconstant(self, name, version):
        return self._get_intern(name)
    def get(self, name):
        self = hint(self, promote=True)
        sc_version = hint(self.semiconstant_version, promote=True)
        
        if self._is_semiconstant(name, sc_version):
            return self._get_semiconstant(name, sc_version)
        else:
            return self._get_intern(name)
