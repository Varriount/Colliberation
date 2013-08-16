from colliberation.protocol import CollaborationProtocol
from colliberation.client.factory import CollabClientFactory
from colliberation.document import Document
from colliberation.packets import make_packet
from sublime_utils import views_from_buffer, enable_listener, disable_listener
from sublime_plugin import EventListener
import sublime


class SublimeDocument(Document, EventListener):

    """
    View connecting to sublime text document.
    TODO - Optimize finding/tracking shared views
    """

    def __init__(self, **kwargs):
        self.view = None
        Document.__init__(self, **kwargs)
        self.buffer_id = None
        self.view = None

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

    @property
    def content(self):
        if self.view is not None:
            region = sublime.Region(0, self.view.size())
            return self.view.substr(region)
        return ''

    @content.setter
    def content(self, value):
        if self.view is not None:
            self_view = self.view
            region = sublime.Region(0, self.view.size())

            edit = self_view.start_edit()
            self.view.replace(edit, region, value)
            self_view.end_edit(edit)

    def change_text(self, start, text, end):
        Document.change_text(start, text, end)
        region = sublime.Region(start, end)
        edit = self.view.start_edit()
        self.view.replace(edit, region, text)
        self.view.end_edit(edit)

    def delete_text(self, start, end):
        Document.delete_text(start, end)
        region = sublime.Region(start, end)
        edit = self.view.start_edit()
        self.view.erase(edit, region)
        self.view.end_edit(edit)

    def open(self):
        """
        Enable listening to events,
        Create view and buffer_id
        """
        enable_listener(self)
        if self.buffer_id is None:
            self_view = sublime.active_window().new_file()
            self_view.set_scratch(True)
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


class SublimeCollabProtocol(CollaborationProtocol):
    doc_class = SublimeDocument
    shadow_doc_class = Document

    def connectionMade(self):
        CollaborationProtocol.connectionMade(self)
        add_packet = make_packet('document_added',
                                 document_id=60,
                                 version=80,
                                 document_name='test.py')
        open_packet = make_packet('document_opened',
                                  document_id=60,
                                  version=80)
        text_mod_packet = make_packet('text_modified',
                                      document_id=60,
                                      version=80,
                                      modifications='@@ -0,0 +1,7 @@\n+abcdefg\n')
        self.transport.write(add_packet)
        self.transport.write(open_packet)
        self.transport.write(text_mod_packet)


class SublimeClientFactory(CollabClientFactory):
    client_class = SublimeCollabProtocol
