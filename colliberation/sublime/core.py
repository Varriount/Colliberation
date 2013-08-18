# TODO
# Add documentation
# Verify variable and function names
# Show status messages to user
#

from colliberation.protocol import CollaborationProtocol
from colliberation.client.factory import CollabClientFactory
from colliberation.document import Document
from colliberation.packets import make_packet
from sublime_utils import (
    views_from_buffer, enable_listener, disable_listener, current_view)
from sublime_plugin import EventListener
import sublime


class SublimeDocument(Document, EventListener):

    """
    View connecting to sublime text document.
    TODO - Optimize finding/tracking shared views
    """

    def __init__(self, **kwargs):
        print("Initialized document {0}".format(self))
        self._cache = ''
        self.view = None
        Document.__init__(self, **kwargs)
        self.buffer_id = None
        self.view = None

    # EventListener methods
    def on_close(self, view):
        self_buffer_id = self.buffer_id
        if view.buffer_id() == self_buffer_id:
            print("{0}: View closed. Switching...".format(self))
            available_views = views_from_buffer(self_buffer_id)
            if available_views:
                self.view = available_views[0]
            elif self.state_deferral is not None:
                print("{0}: Switching failed.".format(self))
                print("{0}: Nulling state_deferral, calling".format(self))
                deferral = self.state_deferral
                self.state_deferral = None
                deferral.callback(self)
            else:
                raise Exception("Ran out of views when not opened")

    # Document methods

    @property
    def content(self):
        print("{0}: Content retrieved".format(self))
        if self.view is not None:
            print("{0}: Using view's content".format(self))
            region = sublime.Region(0, self.view.size())
            return self.view.substr(region)
        else:
            print("{0}: Using cached content.".format(self))
            return self._cache

    @content.setter
    def content(self, value):
        print("{0}: Setting document content".format(self))
        if self.view is not None:
            print("{0}: Directly setting view content".format(self))
            self_view = self.view
            region = sublime.Region(0, self.view.size())

            edit = self_view.begin_edit()
            self.view.replace(edit, region, value)
            self_view.end_edit(edit)
        else:
            print("{0}: Setting cache content".format(self))
            self._cache = value

    def change_text(self, start, text, end):
        print("{0}: Changing text.".format(self))
        Document.change_text(self, start, text, end)
        region = sublime.Region(start, end)
        edit = self.view.begin_edit()
        self.view.replace(edit, region, text)
        self.view.end_edit(edit)

    def delete_text(self, start, end):
        print("{0}: Deleting text.".format(self))
        Document.delete_text(self, start, end)
        region = sublime.Region(start, end)
        edit = self.view.begin_edit()
        self.view.erase(edit, region)
        self.view.end_edit(edit)

    def open(self):
        """
        Enable listening to events,
        Create view and buffer_id
        """
        print("{0}: Opened".format(self))
        enable_listener(self)
        if self.buffer_id is None:
            print("{0}: Empty buffer ID. Creating view.".format(self))
            self_view = sublime.active_window().new_file()
            self_view.set_scratch(True)
            self_view.set_name(self.name)

            self.view = self_view
            self.buffer_id = self_view.buffer_id()
        self.content = self._cache
        return Document.open(self)

    def close(self):
        print("{0}: Closing".format(self))
        disable_listener(self)
        open_views = views_from_buffer(self.buffer_id)
        args = {'group': None, 'index': None}
        for window, view in open_views:
            args['group'], args['index'] = window.get_view_index(view)
            window.run_command("close_by_index", args)

        self._cache = self.content
        self.buffer_id = None
        self.view = None
        self.state_deferral = None
        return Document.close(self)


class SublimeCollabProtocol(CollaborationProtocol):
    doc_class = SublimeDocument
    shadow_doc_class = Document

    def connectionMade(self):
        current_view().set_status("Collaboration", 'Connection made')
        CollaborationProtocol.connectionMade(self)

    def connectionLost(self, reason):
        current_view().set_status(
            "Collaboration",
            "Connection lost. ({0})".format(reason)
        )


class SublimeClientFactory(CollabClientFactory):
    client_class = SublimeCollabProtocol

    def __init__(self, hook):
        CollabClientFactory.__init__(self)
        self.hook = hook

    def startedConnecting(self, connector):
        current_view().set_status(
            'Collaboration',
            'Started Connecting at {0}...'.format(connector))
        self.hook.startedConnecting(connector)

    def clientConnectionFailed(self, connector, reason):
        current_view().set_status(
            'Collaboration',
            'Connection failed at {0} - ({1})'.format(connector, reason)
        )
        self.hook.clientConnectionFailed(connector, reason)

    def clientConnectionLost(self, connector, reason):
        current_view().set_status(
            'Collaboration',
            'Connection lost at {0} - ({1})'.format(connector, reason))

        self.hook.clientConnectionLost(connector, reason)

        destination = connector.getDestination()
        key = destination.host + str(destination.port)
        del(self.protocols[key])

    def startFactory(self):
        print('Factory started')

    def stopFactory(self):
        print('Factory stopped')
