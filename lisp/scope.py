from pypy.rlib.jit import hint, elidable as purefunction

class NameNotSet(Exception):
    pass
class EmptyStack(Exception):
    pass

class VersionTag(object):
    pass

class Scope(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.table = {}
        self.semiconstant_version = VersionTag()
        self.semiconstants = []
        
        if parent is not None:
            self.semiconstants = parent.semiconstants

    @purefunction
    def _is_semiconstant(self, name, version):
        return (name in self.semiconstants)
    
    def is_set(self, name):
        if name in self.table:
            return True
        if self.parent is not None:
            return self.parent.is_set(name)
        return False
    
    def _set_intern(self, name, val, local_only):
        if local_only:
            self.table[name] = val
        else:
            if name in self.table:
                self.table[name] = val
            elif self.parent is not None and self.parent.is_set(name):
                self.parent._set_intern(name, val, False)
            else:
                self.table[name] = val
    def set_semiconstant(self, name, val, local_only=False):
        self = hint(self, promote=True)
        sc_version = hint(self.semiconstant_version, promote=True)
        
        self._set_intern(name, val, local_only)
        if not self._is_semiconstant(name, sc_version):
            self.semiconstants.append(name)
        self.semiconstant_version = VersionTag()
    def set(self, name, val, local_only=False):
        self = hint(self, promote=True)
        sc_version = hint(self.semiconstant_version, promote=True)
        
        if self._is_semiconstant(name, sc_version):
            self.set_semiconstant(name, val)
        else:
            self._set_intern(name, val, local_only)

    def _get_intern(self, name):
        try:
            return self.table[name]
        except KeyError:
            if self.parent is None:
                raise NameNotSet(name)
            return self.parent._get_intern(name)
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
