import sys

_PY3 = sys.version_info[0] == 3

class NullType(object):
    """
    A 'null' type different from, but parallel to, None. Core function
    is representing emptyness in a way that doesn't overload None.
    This helps create designated identifiers with specific meanings
    such as Passthrough, Prohibited, and Undefined.
    
    Instantiate to create desired null singletons. While they are
    singletons, depends on usage convention rather than strict
    enforcement to maintain their singleton-ness. This is a problem
    roughly 0% of the time.
    """
    def __init__(self, name=None):
        self.name = name
        
    def __repr__(self):
        if self.name is not None:
            return self.name
        else:
            return repr(self)

    
    if _PY3:
        def __bool__(self):
            """I am always False."""
            return False
    else: # PY2
        def __nonzero__(self):
            """I am always False."""
            return False