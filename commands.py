from sublime_plugin import ApplicationCommand
import sublime
import sys
import os

# Hack to allow us to import external libraries
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

# Another hack, to incorporate twisteds reactor
from sublime_utils import install_twisted
install_twisted()

# Now back to our regularly scheduled programming
from core import SublimeClientFactory
from sublime_utils import MultiPrompt

"""
To recieve and send events from the editor to the client object,
we pass hooks to the factor
"""


class ColliberationCore(object):

    """
    Core class for sublimetext collaboration components.
    Additionally, the core sinks event hooks into the colliberation client
    and factory, to allow children of this class to respond to events.
    This allows semi-global state to be managed.
    """
    factory = SublimeClientFactory()
    client = None

# Commands


class CollaborationCommand(ApplicationCommand, ColliberationCore):

    """
    Base class for collaboration commands.
    Provides utility functions and such.
    """

    def choose_file(self, callback):
        self.client.update_available_documents()
        sublime.active_window().show_quick_panel(
            self.client.available_documents, callback
        )

    def description(self):
        return self.__doc__().strip('    ').replace('\n', ' ')

    def is_visible(self):
        return self.is_enabled()

    def is_connected(self):
        if self.client is not None:
            return self.client.connected
        return False


class ConnectToServer(CollaborationCommand):

    """
    Connect to a document collaboration server.
    """

    def __init__(self):
        self.connection_prompt = MultiPrompt(
            prompts=[
                ('Server IP Address?', '127.0.0.1'),
                ('Server Port?', '6687'),
            ],
            on_done=self.connect,
            on_change=None,
            on_cancel=None
        )

    def run(self):
        self.connection_prompt.start_prompt()

    def connect(self, results):
        # Validate user input
        address, port = results
        try:
            port = int(port)
        except ValueError:
            sublime.status_message(
                'Invalid address or port : {0}, {1} .'.format(address, port)
            )
        else:
            # Send a connection request to the factory
            sublime.status_message('Connecting to collaboration server...')
            deferred_client = self.factory.connect_to_server(address, port)
            # Attach success and failure callbacks
            deferred_client.addCallback(self.connect_success)
            deferred_client.addErrback(self.connect_fail)

    def connect_success(self, protocol):
        sublime.status_message("Connection Established.")
        self.client = protocol

    def connect_fail(self, error):
        sublime.status_message("Connection failed ({0})".format(error))
        self.client = None

    def is_enabled(self):
        return not self.is_connected()


class DisconnectFromServer(CollaborationCommand):

    """
    Disconnect from a document collaboration server.
    """

    def run(self):
        sublime.status_message('Disconnecting from collaboration server...')
        self.client.transport.loseConnection()
        sublime.status_message('Disconnected from collaboration server.')

    def is_enabled(self):
        return (self.is_connected())


class ListAvailableDocuments(CollaborationCommand):

    """
    List available documents on the collaboration server.
    """

    def run(self):
        self.choose_file(None)

    def is_enabled(self):
        return self.is_connected()


class OpenDocument(CollaborationCommand):

    """
    Open a document available on the collaboration server.
    """

    def run(self):
        self.choose_file(self.open_document)

    def open_document(self, document_id):
        if document_id < 0:
            pass
        else:
            document = self.client.open_document(document_id)
            sublime.status_message('Opening {0}'.format(document))

    def is_enabled(self):
        return self.is_connected()


class RenameDocument(CollaborationCommand):

    """
    Rename a document available on the collaboration server.
    """
    document_id = None

    def run(self):
        self.choose_file(self.step_two)

    def step_two(self, document_id):
        self.document_id = document_id
        sublime.active_window().show_input_panel(
            'New name?', '', self.step_three, None, None
        )

    def step_three(self, input):
        self.client.rename_document(self.document_id, input)

    def is_enabled(self):
        return self.is_connected()


class AddDocument(CollaborationCommand):

    """
    Add a document to the collaboration server.
    """

    def run(self):
        sublime.active_window().show_input_panel(
            "New document name?", "", self.add_document, None, None
        )

    def add_document(self, document_name):
        self.client.create_blank_document(document_name)

    def is_enabled(self):
        return self.is_connected()


class DeleteDocument(CollaborationCommand):

    """
    Delete a document on the collaboration server.
    """

    def run(self):
        self.choose_file(self.delete_document)

    def delete_document(self, document_id):
        self.client.delete_document(document_id)

    def is_enabled(self):
        return self.is_connected()
