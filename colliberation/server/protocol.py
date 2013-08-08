
from colliberation.protocol import CollaborationProtocol
from colliberation.packets import make_packet

WAITING_FOR_AUTH = 1
AUTHORIZED = 2


class CollabServerProtocol(CollaborationProtocol):

    """ A generic protocol to used by the server.

    The server protocol is quite active compared to it's client counterpart.
    It acts on incoming requests, merging in changes, etc.
    """

    def __init__(self, **kwargs):
        CollaborationProtocol.__init__(self, **kwargs)
        self.shadow_docs = {}  # Document copies that match client's snaphots

    def send_available_docs(self):
        pass

    # Document event handlers
    def document_opened(self, data):
        """ Open a document.

        Send a document_opened packet.
        """

        CollaborationProtocol.document_opened(self, data)
        packet = make_packet('document_opened',
                             data.document_id)

        self.factory.broadcast(packet)

    def document_closed(self, data):
        """ Close a document.

        Send a document_closed packet.
        """
        CollaborationProtocol.document_closed(self, data)
        packet = make_packet('document_closed',
                             data.document_id)

        self.factory.broadcast(packet)

    def document_saved(self, data):
        """ Save a document.

        Send a document_saved packet.
        """
        CollaborationProtocol.document_saved(self, data)
        packet = make_packet('document_saved',
                             data.document_id)

        self.factory.broadcast(packet)

    def document_added(self, data):
        """ Add a document.

        Send a document_added packet.
        """
        CollaborationProtocol.document_added(self, data)
        packet = make_packet('document_added',
                             document_id=data.document_id,
                             version=data.version,
                             document_name=data.document_name)

        self.factory.broadcast(packet)

    def document_deleted(self, data):
        """ Delete a document.

        Send a document_deleted packet.
        """
        CollaborationProtocol.document_deleted(self, data)
        packet = make_packet('document_deleted',
                             data.document_id)

        self.factory.broadcast(packet)

    def name_modified(self, data):
        """ Modify the name of a document.

        Send a name_modified packet.
        """
        CollaborationProtocol.name_modified(self, data)
        packet = make_packet('name_modified',
                             data.document_id,
                             data.new_name)

        self.factory.broadcast(packet)

    def content_modified(self, data):
        """ Modify the content of a document.

        Send a content_modified packet.
        """
        CollaborationProtocol.content_modified(self, data)
        packet = make_packet('content_modified',
                             data.document_id,
                             data.modifications)

        self.factory.broadcast(packet)

    def metadata_modified(self, data):
        """ Modify the metadata of a document.

        Send a metadata_modified packet.
        """
        CollaborationProtocol.metadata_modified(self, data)
        packet = make_packet('metadata_modified',
                             data.document_id,
                             data.type,
                             data.key,
                             data.value)

        self.factory.broadcast(packet)

    def version_modified(self, data):
        """ Modify the version of a document.

        Send a version_modified packet.
        """
        CollaborationProtocol.version_modified(self, data)
        packet = make_packet('version_modified',
                             data.document_id,
                             data.version)

        self.factory.broadcast(packet)
