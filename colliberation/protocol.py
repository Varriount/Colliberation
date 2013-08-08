from twisted.internet.protocol import Protocol
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.task import LoopingCall

from colliberation.packets import parse_packets, make_packet
from colliberation.document import Document
from colliberation.serializer import DiskSerializer
from colliberation.utils import pipeline_funcs

from diff_match_patch import diff_match_patch as DMP

from warnings import warn

dmp = DMP()
WAITING_FOR_AUTH = 1
AUTHORIZED = 2


class BaseCollaborationProtocol(Protocol, TimeoutMixin):

    """ A symmetric, nearly stateless protocol used by collaboration clients
    and servers.

    This class serves as a skeletion, only implementing the core
    event handlers and hooks.
    """
    timeout_rate = 60
    connected = False

    def __init__(self, **kwargs):
        """ Set up the protocol.

        This involves:
            - Setting the timeout
            - Creating the data buffer
            - Setting the packet handlers

        """
        self.setTimeout(kwargs.get('timeout', self.timeout_rate))
        self.factory = kwargs.get('factory', None)
        self.address = kwargs.get('address', None)

        self.buffer = ""

        self.packet_handlers = {
            # Utility actions
            0: self.ping_recieved,
            4: self.handshake_recieved,
            5: self.message_recieved,
            6: self.error_recieved,

            # Document actions
            10: self.document_opened,
            11: self.document_closed,
            12: self.document_saved,
            13: self.document_added,
            14: self.document_deleted,
            15: self.document_renamed,

            # Document content actions
            20: self.text_modified,
            21: self.metadata_modified,
        }

    def dataReceived(self, data):
        self.buffer += data

        packets, self.buffer = parse_packets(self.buffer)

        if packets:
            self.resetTimeout()

        for header, payload in packets:
            if header in self.packet_handlers:
                self.packet_handlers[header](payload)
            else:
                print("Couldn't handle parseable packet %d!" % header)
                print(payload)

    def connectionMade(self):
        self.connected = True

    def connectionLost(self, reason):
        self.connected = False

    def timeoutConnection(self):
        pass

    # Misc. event handlers
    def handshake_recieved(self, name):
        pass

    def ping_recieved(self, timestamp):
        pass

    def message_recieved(self, message):
        pass

    def error_recieved(self, error_type, message):
        pass

    # Document event handlers
    def document_opened(self, document_id, version):
        pass

    def document_closed(self, document_id, version):
        pass

    def document_saved(self, document_id, version):
        pass

    def document_added(self, document_id, version, document_name):
        pass

    def document_deleted(self, document_id, version):
        pass

    def document_renamed(self, document_id, new_name):
        pass

    # Document content event handlers
    def text_modified(self, document_id, version, modifications):
        pass

    def metadata_modified(self, document_id, version, type, key, value):
        pass


# Generic protocol implementation

class CollaborationProtocol(BaseCollaborationProtocol):

    """ A generic colliberation client protocol.

    A colliberation client protocol mostly acts on orders from the server, only
    acting when it gets appropriate messages from the server, even if the
    orders are in reaction to a message it sent originally.
    """
    # Template classes
    doc_class = Document
    serializer_class = DiskSerializer

    # Default settings
    username = ''
    password = ''

    def __init__(self, **kwargs):
        BaseCollaborationProtocol.__init__(self)
        # Document datas
        self.open_docs = kwargs.get('open_docs', {})  # id : Doc
        self.available_docs = kwargs.get('available_docs', {})  # id : Doc

        # Internal objects
        self.serializer = self.serializer_class()

        # Client information
        self.state = WAITING_FOR_AUTH

        # Start pinging server to maintain connection
        self.ping_loop = None

        # Setup hooks

        # Message hooks
        self.message_hooks = kwargs.get('message_hooks', [])
        self.error_hooks = kwargs.get('error_hooks', [])

        # Document hooks
        self.doc_add_hooks = kwargs.get('doc_add_hooks', [])
        self.doc_delete_hooks = kwargs.get('doc_delete_hooks', [])
        self.doc_save_hooks = kwargs.get('doc_save_hooks', [])
        self.doc_open_hooks = kwargs.get('doc_open_hooks', [])
        self.doc_close_hooks = kwargs.get('doc_close_hooks', [])

        # Document content hooks
        self.text_mod_hooks = kwargs.get('text_mod_hooks', [])
        self.name_mod_hooks = kwargs.get('name_mod_hooks', [])
        self.metadata_mod_hooks = kwargs.get('metadata_mod_hooks', [])
        self.version_mod_hooks = kwargs.get('version_mod_hooks', [])

    # Protocol Event Handlers
    def connectionMade(self):
        """ Called when a connection is made.

        The protocol starts the handshake process, sending information about
        itself to the connecter. It then starts the pingback loop, which
        maintains the connection.
        """
        ping_packet = make_packet('ping', id=0)
        self.ping_loop = LoopingCall(
            self.transport.write,
            ping_packet
        )
        self.ping_loop.start(self.timeout_rate)

        packet = make_packet('handshake', username=self.username)
        self.transport.write(packet)

    # Misc. event handlers
    def handshake_recieved(self, data):
        """
        If we are waiting, set the username.
        Else, send error packet.
        """

        if self.state == WAITING_FOR_AUTH:
            self.state = AUTHORIZED
            self.other_name = data.username

    def message_recieved(self, data, func_hooks=None):
        """
        Print message
        """
        if func_hooks is None:
            hooks = self.message_hooks

        message = data.message
        message = pipeline_funcs(hooks, message)
        if message is not None:
            print(message)
            return True
        return False

    def error_recieved(self, data, func_hooks=None):
        """
        Print message.
        """
        if func_hooks is None:
            hooks = self.error_hooks

        message = data.message
        message = pipeline_funcs(hooks, message)
        if message is not None:
            warn(message)
            return True
        return False

    # Document event handlers
    def document_opened(self, data, func_hooks=None):
        """ Open a document.

        We transfer the document object from available_docs to
        open documents. If the document is not in available_docs, send
        out a warning.
        Hooks:
            Pipeline Hooks
        """
        if func_hooks is None:
            hooks = self.doc_open_hooks

        if data.document_id not in self.available_docs:
            self._warn_doc_not_available(data.document_id)
            self.document_added(data)

        document = self.available_docs.pop(data.document_id)
        document = pipeline_funcs(hooks, document)

        if document is not None:
            self.open_docs[data.document_id] = document
            return True
        return False

    def document_closed(self, data, func_hooks=None):
        """ Close a document.

        We transfer the doc from open_docs to available_docs. If the document
        is not found, raise a warning.
        """
        if func_hooks is None:
            hooks = self.doc_close_hooks

        if data.document_id not in self.open_docs:
            self._warn_doc_not_open(data.document_id)
        else:
            document = self.open_docs.pop(data.document_id)
            document = pipeline_funcs(hooks, document)

            if document is not None:
                self.available_docs[data.document_id] = document
                return True
        return False

    def document_saved(self, data, func_hooks=None):
        """ Save a document

        We try calling the serializer on the selected document,
        warning if the document is not open.
        """
        if func_hooks is None:
            hooks = self.doc_save_hooks

        if data.document_id not in self.open_docs:
            self._warn_doc_not_open(data.document_id)
        else:
            document = self.open_docs[data.document_id]
            document = pipeline_funcs(hooks, document)
            if document is not None:
                self.serializer.save_document(document)
                return True
        return False

    def document_added(self, data, func_hooks=None):
        """ Add a document.

        Create and add a new document to the available document list,
        raising a warning if the document already exists.
        """
        if func_hooks is None:
            hooks = self.doc_add_hooks

        if data.document_id in self.available_docs:
            warn('Document {} already exists'.format(data.document_id))
        else:
            document = self.doc_class(id=data.document_id)
            document = pipeline_funcs(hooks, document)
            if document is not None:
                self.available_docs[data.document_id] = document
                return True
        return False

    def document_deleted(self, data, func_hooks=None):
        """ Delete a document.

        If it's a document we have open,and close it.
        Remove the document from the available documents list.
        """
        self.document_closed(data)
        if data.document_id in self.available_docs:
            del(self.available_docs[data.document_id])
        else:
            warn('Deleted Document ID {} not in available documents'
                 .format(data.document_id))

    # Document content event handlers.

    def name_modified(self, data):
        """ Rename a document.

        Find the document in open_docs or available_docs, and modify it's
        name variable, raising a warning if the document cannot be found.
        """
        document = None
        if data.document_id in self.open_docs:
            document = self.open_docs[data.document_id]
        elif data.document_id in self.available_docs:
            document = self.available_docs[data.document_id]
        else:
            warn('Document {} cannot be found'.format(data.document_id))
        if document:
            document.name = data.new_name

    def text_modified(self, data):
        """ Modify the text in the document.

        Retrieve the document open_docs, and patch it with the given patches.
        """
        if data.document_id not in self.open_docs:
            self._warn_doc_not_open(data.document_id)
        else:
            patches = dmp.patch_fromText(data.modifications)
            document = self.open_docs[data.document_id]
            document.patch(patches)

    def metadata_modified(self, data, func_hooks=None):
        """
        Modify the metadata in the specified document.
        """
        if func_hooks is None:
            hooks = self.metadata_mod_hooks

        if data.document_id not in self.open_docs:
            self._warn_doc_not_open(data.document_id)
        else:
            document = self.open_docs[data.document_id]
            metadata = pipeline_funcs(
                hooks, document, cancellable=True, stoppable=True)
            document.metadata[data.key] = data.value

    def version_modified(self, data):
        if data.document_id not in self.open_docs:
            self._warn_doc_not_open(data.document_id)
        else:
            document = self.open_docs[data.document_id]
            document.version = data.version

    def _warn_doc_not_open(self, document_id):
        warn('Document {} not found in open_docs'.format(document_id))

    def _warn_doc_not_available(self, document_id):
        warn('Document {} not found in available_docs'.format(document_id))
