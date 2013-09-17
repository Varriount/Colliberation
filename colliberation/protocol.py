from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.task import LoopingCall

from colliberation.packets import parse_packets, make_packet
from colliberation.workspace import Workspace
from colliberation.document import Document
from colliberation.serializer import DiskSerializer
from colliberation.utils import pipeline_funcs

from diff_match_patch import diff_match_patch as DMP

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

DEBUG = False


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

        Setting up the protocol involves setting up control structures, such
        as the packet handlers, and various connection specific settings,
        such as the timeout period.

        Note:
            If overriding this method, subclasses are
            *strongly* advised to use super() to call this method.

        Arguments:
            kwargs: Keyword arguments for protocol settings.
            Valid Keys:
                - 'factory' : The source factory that built the protocol
                - 'address' : Address object representing the protocol's source
                - 'timeout' : The timeout length.

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
        """ Core event handler for incoming connection data.

        This method handles all incoming data, parses it, and calls the
        appropriate event handler with the parsed data.

        Arguments:
            data (str): Bytestring of incoming data.
        """
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
        """ Called when a connection is made with this protocol's source. """
        self.connected = True

    def connectionLost(self, reason):
        """ Called when this protocol's host connection is lost, usually by
        deliberate disconnection.

        Arguments:
            reason: Reason for the lost connection.
        """
        self.connected = False
        self.cleanup(self)

    def timeoutConnection(self):
        """ Called when this protocol's host connection times out."""
        self.connected = False
        self.cleanup(self)

    # Misc. event handlers
    def handshake_recieved(self, data):
        """ Called when the protocol recieves a handshake packet.

        Arguments:
            data: Parsed packet data. See packets.handshake
        """
        raise NotImplementedError

    def ping_recieved(self, data):
        """ Called when the protocol recieves a ping packet.

        Arguments:
            data: Parsed packet data. See packets.ping
        """
        raise NotImplementedError

    def message_recieved(self, data):
        """ Called when the protocol recieves a message packet.

        Arguments:
            data: Parsed packet data. See packets.message
        """
        raise NotImplementedError

    def error_recieved(self, data):
        """ Called when the protocol recieves an error packet.

        Arguments:
            data: Parsed packet data. See packets.error
        """
        raise NotImplementedError

    # Document event handlers
    def document_opened(self, data):
        """ Called when the protocol recieves a document_opened packet.

        Arguments:
            data: Parsed packet data. See packets.document_opened
        """
        raise NotImplementedError

    def document_closed(self, data):
        """ Called when the protocol recieves a document_closed packet.

        Arguments:
            data: Parsed packet data. See packets.document_closed
        """
        raise NotImplementedError

    def document_saved(self, data):
        """ Called when the protocol recieves a document_saved packet.

        Arguments:
            data: Parsed packet data. See packets.document_saved
        """
        raise NotImplementedError

    def document_added(self, data):
        """ Called when the protocol recieves a document_added packet.

        Arguments:
            data: Parsed packet data. See packets.document_added
        """
        raise NotImplementedError

    def document_deleted(self, data):
        """ Called when the protocol recieves a document_deleted packet.

        Arguments:
            data: Parsed packet data. See packets.document_deleted
        """
        raise NotImplementedError

    def name_modified(self, data):
        """ Called when the protocol recieves a name_modified packet.

        Arguments:
            data: Parsed packet data. See packets.name_modified
        """
        raise NotImplementedError

    # Document content event handlers
    def text_modified(self, data):
        """ Called when the protocol recieves a text_modified packet.

        Arguments:
            data: Parsed packet data. See packets.text_modified
        """
        raise NotImplementedError

    def metadata_modified(self, data):
        """ Called when the protocol recieves a metadata_modified packet.

        Arguments:
            data: Parsed packet data. See packets.metadata_modified
        """
        raise NotImplementedError

    def version_modified(self, data):
        """ Called when the protocol recieves a version_modified packet.

        Arguments:
            data: Parsed packet data. See packets.version_modified
        """
        raise NotImplementedError

# Generic protocol implementation


class CollaborationProtocol(BaseCollaborationProtocol):

    """ A generic colliberation client protocol.

    A colliberation client protocol mostly acts on orders from the server, only
    acting when it gets appropriate messages from the server, even if the
    orders are in reaction to a message it sent originally.

    Currently, the specific class attributes are used to define what classes
    are to be used by the protocol to fulfill certain functionality.
    the various classes.
    """

    # Template classes
    workspace_class = Workspace
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
        self.workspaces = kwargs.get('workspaces', {})
        self.current_workspace = kwargs.get('current_workspace', None)

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

        In addition to the preparations made by
        :ref:class:BaseCollaborationProtocol, the protocol starts the handshake
        process, sending information about itself to the connecter.
        It then starts the pingback loop, in order to maintain the connection.
        """
        ping_packet = make_packet('ping', id=0)
        self.ping_loop = LoopingCall(
            self.transport.write,
            ping_packet
        )
        self.ping_loop.start(self.timeout_rate)

        packet = make_packet('handshake', username=self.username)
        self.transport.write(packet)

    def cleanup(self):
        """
        Cleanup a the protocol's resources.
        """
        self.ping_loop.stop()
        self.ping_loop = None

    # Misc. event handlers
    def ping_recieved(self, data):
        pass

    def handshake_recieved(self, data):
        """ Responds to the handshake by setting the username and
        authorization switch.
        """
        if self.state == WAITING_FOR_AUTH:
            self.state = AUTHORIZED
            self.other_name = data.username

    def message_recieved(self, data, func_hooks=None):
        """ Prints the recieved message to stdout. """
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
        """ Prints the recieved error to stdout. """
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
        """ Opens a document.

        Retrieves the document object from self.available_docs to
        self.open_documents, and creates a shadow copy, if one doesn't already
        exist.
        """

        if func_hooks is None:
            hooks = self.doc_open_hooks

        # Plugins
        document = self.current_workspace.retrieve_document(data.document_id)

        document = pipeline_funcs(
            hooks,
            document,
            can_stop=True,
            can_cancel=True
        )

        # Action
        if document is not None:
            shadow = self.shadow_class()
            shadow.update(document)

            self.open_docs[data.document_id] = document
            self.shadow_docs[data.document_id] = shadow

            d = document.open()
            d.addCallback(self.doc_callback)
            return True
        return False

    def doc_callback(self, document):
        """ Callback for open_documents to signal that they've been closed. """
        p = make_packet('document_closed',
                        document_id=document.id,
                        hash=document.version,
                        workspace_id=document.id)
        self.transport.write(p)

    def document_closed(self, data, func_hooks=None):
        """ Close a document.

        Removes the document from self.open_docs and self.shadow_docs.
        """
        # Preconditions
        assert data.document_id in self.open_docs
        assert data.document_id in self.shadow_docs
        if func_hooks is None:
            hooks = self.doc_close_hooks

        document = self.open_docs.pop(data.document_id)
        self.shadow_docs.pop(data.document_id)
        document = pipeline_funcs(
            hooks,
            document,
            can_stop=True,
            can_cancel=True
        )
        document.close()

        return (document is not None)

    def document_saved(self, data, func_hooks=None):
        """ Save a document

        Calls the serializer on the selected document.
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

        Creates and adds a new document to self.available_docs, raising a
        warning if the document already exists.
        """
        if func_hooks is None:
            hooks = self.doc_add_hooks

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
            self.current_workspace.add_document(document)
            return True
        return False

    def document_deleted(self, data, func_hooks=None):
        """ Delete a document.

        Closes the indicated document, and then removes it from
        self.available_docs.
        """
        self.document_closed(data)
        self.current_workspace.remove_document(data.document_id)

    # Document content event handlers.
    # These handlers send data back to sender based on whether they
    # recieved data merges correctly.

    def name_modified(self, data):
        """ Rename a document.

        Finds document in open_docs or available_docs and modifies it's name,
        raising a warning if the document cannot be found.
        """

        document = self.current_workspace.retrieve_document(data.document_id)
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
                can_cancel=True,
                can_stop=True
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
