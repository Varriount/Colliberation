from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.task import LoopingCall

from colliberation.packets import parse_packets, make_packet
from colliberation.document import Document
from colliberation.serializer import DiskSerializer
from colliberation.utils import pipeline_funcs

from diff_match_patch import diff_match_patch as DMP

from warnings import warn

flexible_dmp = DMP()
fragile_dmp = DMP()
fragile_dmp.Match_Threshold = 0.0
fragile_dmp.Match_Distance = 0.0
fragile_dmp.Patch_DeleteThreshold = 0.0

WAITING_FOR_AUTH = 1
AUTHORIZED = 2

# Logging strings
DOC_NOT_AVAILABLE = 'Document with ID {0} is not available.'
DOC_NOT_OPEN = 'Document with ID {0} is not open.'

DEBUG = True


def log(text):
    if DEBUG:
        print(text)


class BaseCollaborationProtocol(Protocol, TimeoutMixin):

    """ A symmetric protocol used by collaboration clients
    and servers.

    This class serves as a skeletion, only implementing the core
    event handlers and hooks.
    """
    timeout_rate = 60
    send_delay = .25
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
            15: self.name_modified,

            # Document content actions
            20: self.text_modified,
            21: self.metadata_modified,
            22: self.version_modified,
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
                log("Couldn't handle parseable packet %d!" % header)
                log(payload)

    def connectionMade(self):
        self.connected = True

    def connectionLost(self, reason):
        self.connected = False

    def timeoutConnection(self):
        self.connected = False

    # Misc. event handlers
    def handshake_recieved(self, data):
        raise NotImplementedError

    def ping_recieved(self, data):
        raise NotImplementedError

    def message_recieved(self, data):
        raise NotImplementedError

    def error_recieved(self, data):
        raise NotImplementedError

    # Document event handlers
    def document_opened(self, data):
        raise NotImplementedError

    def document_closed(self, data):
        raise NotImplementedError

    def document_saved(self, data):
        raise NotImplementedError

    def document_added(self, data):
        raise NotImplementedError

    def document_deleted(self, data):
        raise NotImplementedError

    def name_modified(self, data):
        raise NotImplementedError

    # Document content event handlers
    def text_modified(self, data):
        raise NotImplementedError

    def metadata_modified(self, data):
        raise NotImplementedError

    def version_modified(self, data):
        raise NotImplementedError

# Generic protocol implementation


class CollaborationProtocol(BaseCollaborationProtocol):

    """ A generic colliberation client protocol.

    A colliberation client protocol mostly acts on orders from the server, only
    acting when it gets appropriate messages from the server, even if the
    orders are in reaction to a message it sent originally.
    """
    # Template classes
    doc_class = Document
    shadow_class = Document
    serializer_class = DiskSerializer

    # Default settings
    username = ''
    password = ''

    # ID
    latest_id = 0

    def __init__(self, **kwargs):
        BaseCollaborationProtocol.__init__(self, **kwargs)
        # Document datas
        self.open_docs = kwargs.get('open_docs', {})  # id : Doc
        self.shadow_docs = kwargs.get('shadow_docs', {})
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
    def ping_recieved(self, data):
        pass

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
        message = pipeline_funcs(
            hooks,
            message,
            can_stop=True,
            can_cancel=True
        )
        if message is not None:
            log(message)
            return True
        return False

    def error_recieved(self, data, func_hooks=None):
        """
        Print message.
        """
        if func_hooks is None:
            hooks = self.error_hooks

        message = data.message
        message = pipeline_funcs(
            hooks,
            message,
            can_stop=True,
            can_cancel=True
        )
        if message is not None:
            log(message)
            return True
        return False

    # Document event handlers
    def document_opened(self, data, func_hooks=None):
        """ Open a document.

        We retrieve the document object from available_docs to
        open_documents, and create a shadow copy if one doesn't exist.
        """
        if func_hooks is None:
            hooks = self.doc_open_hooks

        document = self.available_docs[data.document_id]
        shadow = self.shadow_class()
        shadow.update(document)
        document = pipeline_funcs(
            hooks,
            document,
            can_stop=True,
            can_cancel=True
        )

        if document is not None:
            self.open_docs[data.document_id] = document
            self.shadow_docs[data.document_id] = shadow
            d = document.open()
            # TODO - Does shadow.open and close need to be called?
            d.addCallback(self.doc_callback)
            return True
        return False

    def doc_callback(self, document):
        p = make_packet('document_closed',
                        document_id=document.id,
                        version=document.version)
        self.transport.write(p)

    def document_closed(self, data, func_hooks=None):
        """ Close a document.

        We remove the doc from open_docs and shadow_docs.
        """
        if func_hooks is None:
            hooks = self.doc_close_hooks
        if data.document_id not in self.open_docs:
            log(
                DOC_NOT_OPEN.format(data.document_id)
            )
            return

        document = self.open_docs.pop(data.document_id)
        self.shadow_docs.pop(data.document_id)
        document = pipeline_funcs(
            hooks,
            document,
            can_stop=True,
            can_cancel=True
        )
        document.close()

        if document is not None:
            self.available_docs[data.document_id] = document
            return True
        return False

    def document_saved(self, data, func_hooks=None):
        """ Save a document

        We try calling the serializer on the selected document.
        """
        if func_hooks is None:
            hooks = self.doc_save_hooks
        if data.document_id not in self.open_docs:
            log(
                DOC_NOT_OPEN.format(data.document_id)
            )
            return

        document = self.open_docs[data.document_id]
        document = pipeline_funcs(
            hooks,
            document,
            can_stop=True,
            can_cancel=True
        )
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
            warn('Document {0} already exists'.format(data.document_id))
        else:
            document = self.doc_class(id=data.document_id,
                                      version=data.version,
                                      name=data.document_name)
            document = pipeline_funcs(
                hooks,
                document,
                can_stop=True,
                can_cancel=True
            )
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
            log(
                DOC_NOT_AVAILABLE.format(data.document_id)
            )

    # Document content event handlers.
    # These handlers send data back to sender based on whether they
    # recieved data merges correctly.

    def name_modified(self, data):
        """ Rename a document.

        Find the document in open_docs or available_docs, and modify it's
        name variable, raising a warning if the document cannot be found.
        """
        if data.document_id not in self.available_docs:
            log(
                DOC_NOT_AVAILABLE.format(data.document_id)
            )
            return

        document = self.available_docs[data.document_id]
        document.name = data.new_name

    def text_modified(self, data):
        """ Modify the text in the document.

        Retrieves the open document and its shadow, and performs a
        flexible and fragile patch using the sent data, respectively.
        A diff of the shadow and the open document is then sent back
        across the wire. The shadow is then updated with the open
        documents content.
        This event handler is unique in that it sends data back to the caller.
        """
        if data.document_id not in self.open_docs:
            log(
                DOC_NOT_OPEN.format(data.document_id)
            )
            return

        log('{0}: Recieved text modifications:'.format(self))
        log(data.modifications)

        d_patches = flexible_dmp.patch_fromText(data.modifications)
        s_patches = fragile_dmp.patch_fromText(data.modifications)

        document = self.open_docs[data.document_id]
        shadow = self.shadow_docs[data.document_id]

        log('{0}: Document text before modification:'.format(self))
        log(document.content)
        log('{0}: Shadow text before modification:'.format(self))
        log(shadow.content)

        # Add plugin call here
        document.patch(d_patches, dmp=flexible_dmp)
        shadow.patch(s_patches, dmp=fragile_dmp)

        log('{0}: Document text after modification:'.format(self))
        log(document.content)
        log('{0}: Shadow text after modification:'.format(self))
        log(shadow.content)
        assert(str(hash(shadow.content)) == data.hash)

        mods = fragile_dmp.patch_toText(
            shadow.make_patches(document.content, fragile_dmp)
        )
        shadow.update(document)

        log('{0}: Sending modifications:'.format(self))
        log(mods)

        reactor.callLater(
            self.send_delay,
            self.transport.write,
            make_packet(
                'text_modified',
                document_id=data.document_id,
                version=document.version,
                modifications=mods,
                hash=str(hash(shadow.content))
            )
        )

    def metadata_modified(self, data, func_hooks=None):
        """
        Modify the metadata in the specified document.
        """
        if data.document_id not in self.open_docs:
            log(
                DOC_NOT_OPEN.format(data.document_id)
            )
            return

        if func_hooks is None:
            hooks = self.metadata_mod_hooks

        if data.document_id not in self.open_docs:
            self._warn_doc_not_open(data.document_id)
        else:
            document = self.open_docs[data.document_id]
            metadata = pipeline_funcs(
                hooks,
                document,
                cancellable=True,
                stoppable=True
            )
            document.metadata[data.key] = data.value

    def version_modified(self, data):
        if data.document_id not in self.open_docs:
            log(
                DOC_NOT_OPEN.format(data.document_id)
            )
            return

        document = self.open_docs[data.document_id]
        document.version = data.version
