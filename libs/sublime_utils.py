import sublime
from sublime_plugin import all_callbacks
from collections import deque


def current_view():
    """
    Retrieve the current active view.
    """
    return sublime.active_window().active_view()


def install_twisted(interval=1, start_running=True):
    try:
        from twisted.internet import _threadedselect
        _threadedselect.install()

        def waker(func):
            sublime.set_timeout(func, interval)

        from twisted.internet import reactor
        reactor.interleave(waker)
    except ImportError:
        return False
    return True


def enable_listener(listener):
    """
    Enable an event listener, registering it with the sublime core and
    allowing it to recieve events.
    """
    dir_listener = dir(listener)
    for callback_label, callback_list in all_callbacks.iteritems():
        if listener not in callback_list:
            if callback_label in dir_listener:
                callback_list.append(listener)


def disable_listener(listener):
    """
    Disable an event listener, stopping it from recieving events.
    """
    for callback_label, callback_list in all_callbacks.iteritems():
        if listener in callback_list:
            if callback_label in dir(listener):
                callback_list.remove(listener)


def retrieve_views(condition):
    """
    Retrieve views following the given conditionary function, which is passed
    a series of view and windows
    """
    return [(view, window)
            for window in sublime.windows()
            for view in window.views()
            if condition(view, window)
            ]


def views_from_buffer(buffer_id):
    """
    Return views that match the given buffer id.
    """
    def buffer_compare(view, window):
        return view.buffer_id == buffer_id
    return retrieve_views(buffer_compare)


def repeat_callback(check_condition,
                    success_func, interval_func, fail_func,
                    max_iterations, delay):
    """
    A conditionary callback.
    """
    count = 0
    limited = (max_iterations > 0)

    def _conditionary_call(iteration_count):
        if limited:
            count = iteration_count + 1
        else:
            count = 0

        if check_condition():
            if success_func is not None:
                success_func()

        else:
            if interval_func is not None:
                interval_func()
                if count <= max_iterations:
                    sublime.set_timeout(
                        lambda: _conditionary_call(count), delay)
                else:
                    fail_func()
    sublime.set_timeout(lambda: _conditionary_call(count), delay)


class MultiPrompt(object):

    """
    Allows a function to gather input from multiple sublime text 2 prompts.
    """

    def __init__(self, prompts, on_done, on_change, on_cancel,
                 window=None):
        if window is None:
            window = sublime.active_window
        self.retrieve_window = window
        self.prompts = prompts
        self.results = []
        self.on_done = on_done
        self.on_change = on_change
        self.on_cancel = on_cancel
        self.depth = 0

    def start_prompt(self):
        self.depth = 0
        self.results = []

        prompt, default = self.prompts[self.depth]
        self.retrieve_window().show_input_panel(
            prompt, default, self._prompt, self.on_change, self.on_cancel)

    def _prompt(self, input):
        """
        """
        self.results.append(input)
        self.depth += 1
        if self.depth < len(self.prompts):
            prompt, default = self.prompts[self.depth]
            self.retrieve_window().show_input_panel(
                prompt, default, self._prompt, self.on_change, self.on_cancel)
        else:
            self.on_done(self.results)
