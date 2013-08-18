from colliberation.protocol import CollaborationProtocol
from colliberation.sublime.document import SublimeDocument

from sublime_utils import current_view


class SublimeCollabProtocol(CollaborationProtocol):
    doc_class = SublimeDocument

    def connectionMade(self):
        current_view().set_status("Collaboration", 'Connection made')
        CollaborationProtocol.connectionMade(self)

    def connectionLost(self, reason):
        current_view().set_status(
            "Collaboration",
            "Connection lost. ({0})".format(reason)
        )
