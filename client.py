from colliberation.protocol import CollaborationProtocol, fragile_dmp
from bidict import Bidict
from sublime_utils import views_from_buffer
import sublime


class SublimeCollabProtocol(CollaborationProtocol):

    def __init__(self, **kwargs):
        CollaborationProtocol.__init__(self)
        self.doc_buffers = Bidict()  # Mapping of doc ID's to buffer ID's

    def document_opened(self, data, func_hooks=None):
        """
        In addition, a new view is opened representing the document, and
        the document's id is mapped to the view's buffer ID
        """
        result = CollaborationProtocol.document_opened(data, func_hooks)
        if result:
            doc = self.open_docs[data.document_id]
            view = sublime.active_window().new_file()
            view.set_scratch(True)
            view.set_name(doc.name)
            self.doc_buffers[data.document_id] = view.buffer_id()
        else:
            sublime.set_status("Document could not be opened.")

    def document_closed(self, data, func_hooks=None):
        """
        In addition, the all views associated with the closed document are
        themselves closed.
        """
        result = CollaborationProtocol.document_opened(data, func_hooks)
        if result:
            document_id = data.document_id
            buffer_id = self.doc_buffers[document_id]

            for window in sublime.windows():
                for view in window.views():
                    if view.buffer_id == buffer_id:
                        group, index = window.get_view_index(view)
                        args = {'group': group, 'index': index}
                        window.run_command("close_by_index", args)

    def text_modified(self, data):
        document_id = data.document_id
        document = self.open_docs[document_id]
        buffer_id = self.doc_buffers[document_id]
        view = views_from_buffer(buffer_id).next()
        region = sublime.Region(0, view.size())

        # This is a hack. Instead, create regions
        document.content = view.substr(region)
        CollaborationProtocol.text_modified(self, data)

        patches = fragile_dmp.make_patches(view.substr(region),
                                           document.content)
        delta = 0
        for patch in patches:
            print(patch)
