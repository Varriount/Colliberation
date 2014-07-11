
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

    def handshake_recieved(self, data):
        CollaborationProtocol.handshake_recieved(self, data)
        for doc_id, document in self.available_docs.iteritems():
            packet = make_packet(
                'document_added',
                document_id=doc_id,
                version=document.version,
                document_name=document.name
            )
            self.transport.write(packet)

    # Document event handlers
    def document_opened(self, data):
        """ Open a document.

        Send a document_opened packet, then send a text_modified packet,
        since we assume that the document opened on the client end is blank.
        """

        CollaborationProtocol.document_opened(self, data)
        packet = make_packet('document_opened',
                             document_id=data.document_id,
                             version=data.version)

        # TODO - This doesn't take into account if the document has already
        # been modified/is no longer blank.
        mod_packet = make_packet(
            'text_modified',
            document_id=data.document_id,
            version=data.version,
            modifications='',
            hash=str(hash(self.shadow_docs[data.document_id].content))
        )

        self.transport.write(packet)
        self.transport.write(mod_packet)

    def document_closed(self, data):
        """ Close a document.

        Send a document_closed packet.
        """
        CollaborationProtocol.document_closed(self, data)
        packet = make_packet('document_closed',
                             document_id=data.document_id,
                             version=data.version)

        self.transport.write(packet)

    def document_saved(self, data):
        """ Save a document.

        Send a document_saved packet.
        """
        CollaborationProtocol.document_saved(self, data)
        packet = make_packet('document_saved',
                             document_id=data.document_id,
                             version=data.version)

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
                             document_id=data.document_id,
                             version=data.version)

        self.transport.write(packet)

    def name_modified(self, data):
        """ Modify the name of a document.

        Send a name_modified packet.
        """
        CollaborationProtocol.name_modified(self, data)
        packet = make_packet(
            'name_modified',
            document_id=data.document_id,
            version=data.version,
            new_name=data.new_name
        )
        self.factory.broadcast(packet)

    def content_modified(self, data):
        """ Modify the content of a document.

        Send a content_modified packet.
        """
        CollaborationProtocol.content_modified(self, data)

    def metadata_modified(self, data):
        """ Modify the metadata of a document.

        Send a metadata_modified packet.
        """
        CollaborationProtocol.metadata_modified(self, data)
        packet = make_packet('metadata_modified',
                             document_id=data.document_id,
                             type=data.type,
                             key=data.key,
                             value=data.value)

        self.factory.broadcast(packet)

    def version_modified(self, data):
        """ Modify the version of a document.

        Send a version_modified packet.
        """
        CollaborationProtocol.version_modified(self, data)
        packet = make_packet('version_modified',
                             document_id=data.document_id,
                             version=data.version,
                             new_version=data.new_version)

        self.transport.write(packet)
