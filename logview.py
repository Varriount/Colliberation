from logging import Handler, NOTSET
import sublime


class SublimeViewHandler(Handler):

    def __init__(level=NOTSET, view_id=None):
        if view_id is None:
            view = sublime.active_window().new_view()
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
