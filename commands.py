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
from colliberation.packets import make_packet
from colliberation.sublime.factory import SublimeClientFactory

from sublime_utils import MultiPrompt
# Commands


class PsuedoFactory(object):
    factory = None
    connected = False
    client = None

    @classmethod
    def startedConnecting(self, connector):
        print("Started")
        self.connected = True

    @classmethod
    def clientConnectionFailed(self, connector, reason):
        self.connected = False
        # self.client = None

    @classmethod
    def clientConnectionLost(self, connector, reason):
        self.connected = False
        self.client = None


class CollaborationCommand(ApplicationCommand, PsuedoFactory):

    """
    Base class for collaboration commands.
    Provides utility functions and such.
    """
    factory = SublimeClientFactory(PsuedoFactory)

    def choose_file(self, callback=None):
        documents = self.client.available_docs
        choices, conversions = [], []
        if callback is None:
            callback = self.null

        for document in documents.itervalues():
            choices.append(document.name)
            conversions.append(document)

        def conversion_callback(slot):
            if slot is -1:
                callback(None)
            else:
                callback(conversions[slot])

        sublime.active_window().show_quick_panel(
            choices, conversion_callback
        )

    def null(self, item):
        pass

    def description(self):
        return self.__doc__().strip('    ').replace('\n', ' ')

    def is_visible(self):
        return self.is_enabled()

    def is_connected(self):
        if self.client is not None:
            return self.connected
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
            deferred = self.factory.connect_to_server(address, port)
            deferred.addCallback(self.set_client)

    def set_client(self, client):
        PsuedoFactory.client = client

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
        return self.is_connected()


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

    def open_document(self, document):
        if document is None:
            return

        open_packet = make_packet(
            'document_opened',
            document_id=document.id,
            version=document.version)
        self.client.transport.write(open_packet)

        sublime.status_message(
            'Opening {0}'.format(document)
        )

    def is_enabled(self):
        return self.is_connected()


class RenameDocument(CollaborationCommand):

    """
    Rename a document available on the collaboration server.
    """

    def run(self):
        self.choose_file(self.step_two)

    def step_two(self, document):
        def step_three(input):
            name_mod_packet = make_packet(
                'name_modified',
                document_id=document.id,
                version=document.version,
                new_name=input
            )
            self.client.transport.write(name_mod_packet)

        sublime.active_window().show_input_panel(
            'New name?',  # Prompt
            '',  # Default value
            step_three,  # Callback
            None,
            None
        )

    def is_enabled(self):
        return self.is_connected()


class AddDocument(CollaborationCommand):

    """
    Add a document to the collaboration server.
    """

    def run(self):
        sublime.active_window().show_input_panel(
            "New document name?",  # Prompt
            "",  # Default value
            self.add_document,  # Callback
            None,
            None
        )

    def add_document(self, document_name):
        add_packet = make_packet(
            'document_added',
            # Needs a better approach
            document_id=hash(document_name),
            version=0,
            document_name=document_name
        )
        self.client.transport.write(add_packet)

    def is_enabled(self):
        return self.is_connected()


class DeleteDocument(CollaborationCommand):

    """
    Delete a document on the collaboration server.
    """

    def run(self):
        self.choose_file(self.delete_document)

    def delete_document(self, document):
        delete_packet = make_packet(
            'document_deleted',
            document_id=document.id,
            version=document.version
        )
        self.client.transport.write(delete_packet)

    def is_enabled(self):
        return self.is_connected()
