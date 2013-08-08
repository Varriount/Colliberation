"""
Plugin and function utilities.
"""


def pipeline_funcs(functions, data, stoppable=True, cancellable=True):
        """
        Runs data through a pipeline of functions. Similar to map, but runs
        the result of each function through the next function.
        """
        piped_data = data
        proceed = True
        cancel = False

        for hook in functions:

            if cancellable and stoppable:
                proceed, cancel, piped_data = hook(piped_data)
            elif cancellable:
                cancel, piped_data = hook(piped_data)
            elif stoppable:
                proceed, piped_data = hook(piped_data)

            if cancel:
                return None
            if not proceed:
                break
        return piped_data

null = str(object())


def multiget(dictionary, *args, **kwargs):
    for key in args:
        result = dictionary.get(key, null)
        if result is not null:
            return result
    return kwargs['default']
