# sample generator coroutine getting access to its own handle

import functools

def attach_handle(function):
    """
    decorator to create a generator coroutine 
    Note that except for the calll to 'send()', this comes from PEP 342
    """
    @functools.wraps(function)
    def wrapper(*args, **kw):
        generator = function(*args, **kw) 
        result = generator.next() # one to get ready
        result = generator.send(generator) # two to store our own handle   
        return generator        
    return wrapper