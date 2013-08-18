from logging import Handler, NOTSET
import sublime
from sublime_utils import views_from_buffer
from sublime_plugin import EventListener


class SublimeViewHandler(Handler, EventListener):

    def __init__(self, level=NOTSET, view_id=None):
        if view_id is None:
            view = sublime.active_window().new_view()
            self.view = view
            self.buffer_id = view.buffer_id()
        else:
            pass
        Handler.__init__(level)

    def emit(self, record):
        """
        Emit a record.

        """
        try:
            msg = self.format(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class ViewLogger(Handler, EventListener):

    """
    Emits log events to a sublime view, if one is open.
    """

    def __init__(self, level=NOTSET, view_id=None):
        Handler.__init__(self, level)
        self.state_deferral = None
        self.view = None
        self.buffer_id = None
        self.follow_bottom = True
        self.cache = []

    # EventListener methods
    def on_close(self, view):
        self_buffer_id = self.buffer_id
        if view.buffer_id == self_buffer_id:
            available_views = views_from_buffer(self_buffer_id)
            if available_views:
                self.view = available_views[0]
            elif self.state_deferral is not None:
                self.close()
            else:
                raise Exception("Ran out of views when not opened")

    # Document methods

    def emit(self, line):
        view = self.view
        view_size = view.size
        region = sublime.Region(start, view_size())

        edit = self.view.start_edit()
        self.view.insert(edit, region, text)
        self.view.end_edit(edit)

        # If the current viewport is located at the bottom of the file, 
        # scroll down.
        scroll_down = self.view.visible_region.contains(self.view.size())
            self.view.show(self.view.size())


    def open(self):
        """
        Enable listening to events,
        Create view and buffer_id
        """
        enable_listener(self)
        if self.buffer_id is None:
            self_view = sublime.active_window().new_file()
            self_view.set_scratch(True)
            #self_view.set_read_only(True)
            self_view.set_name(self.name)

            self.view = self_view
            self.buffer_id = self_view.buffer_id()

        return Document.open(self)

    def close(self):
        disable_listener(self)
        open_views = views_from_buffer(self.buffer_id)
        args = {'group': None, 'index': None}
        for window, view in open_views:
            args['group'], args['index'] = window.get_view_index(view)
            window.run_command("close_by_index", args)

        self.buffer_id = None
        self.view = None
        return Document.close(self)

