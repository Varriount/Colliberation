"""
Plugin and function utilities.
"""


class Pipeline(object):

    def __init__(self, functions, varargs=None, kwargs=None,
                 can_stop=None, can_cancel=None):
        self.functions = functions
        self.varargs = varargs
        self.kwargs = kwargs

        self.can_cancel = can_cancel
        self.can_stop = can_stop
        self.cancelled = False
        self.stopped = False

    def cancel(self):
        if self.can_cancel:
            self.cancelled = True
        else:
            raise Exception("Pipeline cannot be cancelled")

    def stop(self):
        if self.can_stop:
            self.stopped = True
        else:
            raise Exception("Pipeline cannot be stopped")

    def reset(self):
        self.cancelled = False
        self.stopped = False


def pipeline_funcs(functions, data, can_stop=True, can_cancel=True):
        """
        Runs data through a pipeline of functions. Similar to map, but runs
        the result of each function through the next function.
        """
        piped_data = data
        proceed = True
        cancel = False

        for hook in functions:

            if can_cancel and can_stop:
                proceed, cancel, piped_data = hook(piped_data)
            elif can_cancel:
                cancel, piped_data = hook(piped_data)
            elif can_stop:
                proceed, piped_data = hook(piped_data)

            if cancel:
                return None
            if not proceed:
                break
        return piped_data

null = str(object())
