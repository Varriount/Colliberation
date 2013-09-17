# TODO
# Add documentation
# Clean up variable & function names
# Sort imports
# Finish command interface with core, factory, and protocols
# Allow for multiple clients
#

from sublime_plugin import ApplicationCommand
import sublime

import sys
import platform
import os
import itertools
import functools

# Hack to allow us to import external libraries
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
bit, other = platform.architecture()
bit_path = os.path.join(libs_path, bit)
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)
    sys.path.insert(0, bit_path)

# Another hack, to incorporate twisteds reactor
from sublime_utils import install_twisted
install_twisted()

# Now back to our regularly scheduled programming
from colliberation.sublime.factory import SublimeClientFactory
from colliberation.server.factory import CollabServerFactory
from colliberation.client.factory import CollabClientFactory

from sublime_utils import MultiPrompt

from attach import attach_handle
from copy import copy

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.error import CannotListenError, ConnectionRefusedError
from twisted.internet.endpoints import serverFromString, clientFromString

CLIENT_TO_CLIENT = object()
CLIENT_TO_SERVER = object()

# Template classes
SIMPLE_CLIENT = SublimeClientFactory
SIMPLE_SERVER = CollabServerFactory
COMPLEX_CLIENT = None
COMPLEX_SERVER = None

CLIENT_CONNECTION = None  # When not none, should be a protocol object
SERVER_CONNECTION = None  # When not none, should be a listening port object

CLIENT_CONNECTED = False

MODE = None
# Utility functions


def wrap_protocol(protocol):
    global CLIENT_CONNECTION, SERVER_CONNECTION
    protocol = copy(protocol)
    connectionLost_original = protocol.connectionLost

    @functools.wraps
    def _connectionLost(self, reason):
        global CLIENT_CONNECTION, SERVER_CONNECTION
        CLIENT_CONNECTION = None
        if SERVER_CONNECTION is not None:
            SERVER_CONNECTION.stopListening()
            SERVER_CONNECTION = None
        connectionLost_original(self, reason)
    protocol.connectionLost = _connectionLost
    return protocol


def choose_file(document_dict, callback=None):
    choices, conversions = [], []

    for document in document_dict.itervalues():
        choices.append(document.name)
        conversions.append(document)

    def conversion_callback(slot):
        if slot is -1:
            callback(None)
        elif callback is not None:
            callback(conversions[slot])

    sublime.active_window().show_quick_panel(
        choices, conversion_callback
    )


def choose_open_file(callback=None):
    return choose_file(CLIENT_CONNECTION.open_docs, callback)


def choose_unopened_file(callback=None):
    available_docs = CLIENT_CONNECTION.available_docs
    open_docs = CLIENT_CONNECTION.open_docs

    unopened_docs = dict(available_docs.viewitems() - open_docs.viewitems())
    return choose_file(unopened_docs, callback)


def choose_available_file(callback=None):
    return choose_file(CLIENT_CONNECTION.available_docs, callback)


def formatServiceString(connection_type, **kwargs):
    result_string = connection_type
    result_string += ':%s=%s' * len(kwargs)
    result_string %= tuple(itertools.chain.from_iterable(kwargs.iteritems()))
    return result_string

SIMPLE_CLIENT.client_class = wrap_protocol(SIMPLE_CLIENT.client_class)
# Base commands


class CollaborationCommand(ApplicationCommand):

    """
    Base class for collaboration commands.
    Provides utility functions and such.
    """

    def description(self):
        return self.__doc__().strip('    ').replace('\n', ' ')

    def is_visible(self):
        return self.is_enabled()


class ConnectionCommand(CollaborationCommand):

    """
    A connection command.
    """

    @inlineCallbacks
    def start_server(self, port, **kwargs):
        """
        Starts the server, using a port and address.
        Should be called when one wants to start a server
        """
        global SERVER_CONNECTION
        server_str = formatServiceString('tcp:'+str(port), **kwargs)
        server_point = serverFromString(reactor, server_str)
        SERVER_CONNECTION = yield server_point.listen(self.server())

    @inlineCallbacks
    def start_client(self, port, address, **kwargs):
        """
        Starts the client.
        Should be called when one wants to start a client.
        """
        global CLIENT_CONNECTION

        client_str = formatServiceString(
            'tcp', port=port, host=address, **kwargs
        )
        client_point = clientFromString(reactor, client_str)
        CLIENT_CONNECTION = yield client_point.connect(self.client())

    def stop_server(self):
        """
        Stops the server.
        Should be called when one wants to stop the server.
        """
        global SERVER_CONNECTION

        if SERVER_CONNECTION is not None:
            SERVER_CONNECTION.stopListening()
            SERVER_CONNECTION = None

    def stop_client(self):
        """
        Stops the cleint.
        Should be called when one wants to start the client.
        """
        global CLIENT_CONNECTION

        if CLIENT_CONNECTION is not None:
            CLIENT_CONNECTION.transport.loseConnection()
            CLIENT_CONNECTION = None

# Client-to-Client Specific Commands


class StartAcceptingConnections(ConnectionCommand):

    """
    Start Client-to-Client broadcast mode, accepting incoming connections from
    other clients.
    """
    client = SIMPLE_CLIENT
    server = SIMPLE_SERVER

    def __init__(self):
        self.connect_prompt = MultiPrompt(
            prompts=[
                ('IP Address to bind to? (Optional)', ''),
                ('Server Port?', '6687'),
            ],
            on_done=self.connect,
            on_change=None,
            on_cancel=None
        )

    def run(self):
        self.connect_prompt.start_prompt()

    @inlineCallbacks
    def connect(self, results):
        """
        Start the client and server objects.
        """
        global SERVER_CONNECTION, CLIENT_CONNECTION
        global CONNECTED, BROADCASTING, MODE, CLIENT_TO_CLIENT

        address, port = results
        try:
            if address == '':
                yield self.start_server(port)
                address = '127.0.0.1'
            else:
                yield self.start_server(port, interface=address)

            yield self.start_client(port, address)
        except (ValueError, CannotListenError):
            self.stop_server()
            self.stop_client()
            sublime.status_message(
                'Invalid address or port: {0}, {1} .'.format(port, address)
            )
            return

    def is_enabled(self):
        return (
            (CLIENT_CONNECTION is None) and  # Not connected to anyone
            (SERVER_CONNECTION is None) and  # Not already broadcasting
            (MODE is None)  # Not connected to another client
        )


class StopAcceptingConnections(ConnectionCommand):

    """
    Stop Client-to-Client mode, disconnecting all attached clients.
    """
    client = SIMPLE_CLIENT
    server = SIMPLE_SERVER

    def run(self):
        global MODE
        self.stop_client()
        self.stop_server()
        MODE = None

    def is_enabled(self):
        return (
            (CLIENT_CONNECTION is not None) and  # Connected to internal server
            (SERVER_CONNECTION is not None) and  # Acting as a hub
            (MODE is CLIENT_TO_CLIENT)  # Not connected to another server
        )


class ConnectToClient(ConnectionCommand):

    """
    Directly connect to a recieving collaboration client.
    """
    client = SIMPLE_CLIENT
    server = SIMPLE_SERVER

    def __init__(self):
        self.connect_prompt = MultiPrompt(
            prompts=[
                ('IP Address of client?', '127.0.0.1'),
                ('Server Port?', '6687'),
            ],
            on_done=self.connect,
            on_change=None,
            on_cancel=None
        )

    def run(self):
        self.connect_prompt.start_prompt()

    @inlineCallbacks
    def connect(self, results):
        """
        TODO Consider merging and seperating parts of this code with the above
        connection code.
        """
        global SERVER_CONNECTION, CLIENT_CONNECTION
        global CONNECTED, BROADCASTING, MODE, CLIENT_TO_CLIENT
        address, port = results
        try:
            yield self.start_client(port, address)
        except (ValueError):
            sublime.status_message(
                'Invalid address or port: {0}, {1} .'.format(port, address)
            )
        except (CannotListenError, ConnectionRefusedError) as ex:
            sublime.status_message(
                'Connection could not be established. ({0})'.format(ex)
            )
        else:
            MODE = CLIENT_TO_CLIENT

    def is_enabled(self):
        return (
            # Not connected to server or client
            (SERVER_CONNECTION is None) and
            # Not acting as a hub
            (CLIENT_CONNECTION is None) and
            # Not acting as a hub or server-client
            (MODE is None)
        )


class DisconnectFromClient(CollaborationCommand):

    """
    Disconnect from a collaboration client.
    """

    def run(self):
        global MODE
        self.stop_client()
        MODE = None

    def is_enabled(self):
        return (
            (SERVER_CONNECTION is None),
            (CLIENT_CONNECTION is not None),
            (MODE is CLIENT_TO_CLIENT)
        )

# Client-to-Server specific commands


class ConnectToServer(ConnectionCommand):

    """
    Disconnect from a collaboration client.
    """

    def __init__(self):
        self.connect_prompt = MultiPrompt(
            prompts=[
                ('IP Address of server?', '127.0.0.1'),
                ('Server Port?', '6687'),
            ],
            on_done=self.connect,
            on_change=None,
            on_cancel=None
        )

    @inlineCallbacks
    def connect(self, results):
        """
        TODO Consider merging and seperating parts of this code with the above
        connection code.
        """
        global SERVER_CONNECTION, CLIENT_CONNECTION
        global CONNECTED, BROADCASTING, MODE, CLIENT_TO_CLIENT
        address, port = results
        try:
            yield self.start_client(port, address)
        except (ValueError):
            sublime.status_message(
                'Invalid address or port: {0}, {1} .'.format(port, address)
            )
        except (CannotListenError, ConnectionRefusedError) as ex:
            sublime.status_message(
                'Connection could not be established. ({0})'.format(ex)
            )
        else:
            MODE = CLIENT_TO_SERVER

    def is_enabled(self):
        return (
            (SERVER_CONNECTION is None),
            (CLIENT_CONNECTION is None),
            (MODE is not CLIENT_TO_CLIENT)
        )


class DisconnectFromServer(ConnectionCommand):

    """
    Disconnect from a collaboration client.
    """

    def run(self):
        global MODE
        self.stop_client()
        MODE = None

    def is_enabled(self):
        return (
            (SERVER_CONNECTION is None),
            (CLIENT_CONNECTION is not None),
            (MODE is CLIENT_TO_SERVER)
        )

# Generic Commands


class CreateDocumentFromNewFile(CollaborationCommand):

    """
    Create a document from a new file.
    """

    def run(self):
        global CLIENT_CONNECTION
        # CLIENT_CONNECTION.

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Ask user for file path (default to temp path)
        # Ask user for name
        # Check that name and path are valid
        # Check that file does not exist
        # Create file
        # Send document added packet

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class CreateDocumentFromExistingFile(CollaborationCommand):

    """
    Creates a new document from an existing file.
    """
    # Ask for a path to file

    def __init__(self):
        pass

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        get_window = sublime.active_window
        path = yield get_window().show_input_panel(
            'Path to file?',  # caption,
            '',  # initial_text,
            handle.send,  # on_done,
            None,  # on_change,
            None  # on_cancel
        )
        try:
            with open(path, 'r') as file:
                contents = file.read()
                url = path
                # Get file name from url
                # Send file added packet
                # Send contents modified packet
        except IOError:
            sublime.status_message(
                'Specified file could not be opened.'
            )

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class CreateDocumentFromCurrentFile(CollaborationCommand):

    """
    Create a document from the currently open file.
    """

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Retrieve current document
        # Get document's content, name, and url
        # Check that document doesn't already exist
        # Send document added packet
        # Send contents updated packet

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class DuplicateDocument(CollaborationCommand):

    """
    Duplicate a shared document.
    """

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Ask user to select available document
        # Ask user to select new name
        # Check that name is valid
        # Send document added packet
        # Send document contents modified packet

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class MergeDocument(CollaborationCommand):

    """
    Merge a document into another document.
    """

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Ask user to select two document's
        # Check that document's are not the same
        # Merge contents using DMP
        # Ask if user wants to delete other document (default to no)

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class RenameDocument(CollaborationCommand):

    """
    Rename a document available on the collaboration server.
    """

    def run(self):
        global CLIENT_CONNECTION
        CLIENT_CONNECTION.rename_document()

    @attach_handle
    def prompt_user():
        handle = yield
        # Ask user to select a document
        # Ask user to input a name
        # Verify name
        # Send name mod packet

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class ListAvailableDocuments(CollaborationCommand):

    """
    List available documents on the collaboration server.
    """

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Show unopened documents.

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class ViewDocumentsAsProject(CollaborationCommand):

    """
    View documents as a sublime project. This will open a new window.
    """

    def run(self):
        pass

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class RemoveDocument(CollaborationCommand):

    """
    Remove a document from the available shared documents.
    """

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Ask user to select document
        # Ask for confirmation
        # Send document remove packet

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)


class OpenDocument(CollaborationCommand):

    """
    Open a document available on the collaboration server.
    """

    def run(self):
        pass

    @attach_handle
    def run_prompt(self):
        handle = yield
        # Ask user to select unopened document
        # Send document opened packet

    def is_enabled(self):
        return (CLIENT_CONNECTION is not None)
