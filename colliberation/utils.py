""" Plugin and function utilities.

This module contains various utilities used throughout the
colliberation project.
"""


def pipeline_funcs(functions, data, can_stop, can_cancel):
        """ Runs data through a function pipeline.

        Runs data through a pipeline of functions, returning the end result.
        Similar to map, but runs the result of each function through the next
        function.

        Arguments:
            functions (list): A list of functions to use.
            data (tuple): The data to use as input for the pipeline.
            can_stop (bool): Whether the pipeline can be stopped by a
                function within the pipeline.
            can_cancel (bool):Whether the pipeline can be cancelled by a
                function within the pipeline.

        Returns:
            The output of the function pipeline.

        Notes:
            If the pipeline is stopped, then the data returned is the data
                given by the last function that was called in the pipeline.

            If a pipeline is cancelled, then the result returned is None.
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
