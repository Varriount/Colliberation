from sublime_plugin import ApplicationCommand, EventListener
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
from colliberation.client.factory import CollabClientFactory
from sublime_utils import MultiPrompt, views_from_buffer
from bidict import bidict

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
    factory = CollabClientFactory()
    client = None

    """
    When recieving a message,
        Display it
    When recieving an error,
        Display it
    When requested to open a document,
        Search for the document's file
        Load the file
    When requested to close a document,
    When requested to save a document,
    When requested to add a document,
    When requested to delete a document,
    When requested to modify a document's name,
    When requested to modify a document's content,
        Lookup the view with the corresponding document_id,
    When requested to modify a document's metadata,
    """

# Event Listener

class ColliberationEventListener(EventListener, ColliberationCore):

    """ A dual event listener.
    An event listener for both events in the sublime text editor
    and events in the colliberation client.
    """

    views = bidict()  # View ID : Document ID

    def __init__(self):
        print("Started!")

    def filter_event(method):
        """
        Decorator to filter out unwanted events, by looking up views.
        """

        def _filter_event(self, view):
            if view.id in self.views:
                method(view)
        return _filter_event

    # Sublime Text Events

    @filter_event
    def on_new(self, view):
        pass

    @filter_event
    def on_load(self, view):
        """
        """

    @filter_event
    def on_clone(self, view):
        pass

    @filter_event
    def on_close(self, view):
        """
        Abandon ship, and jump to the next available view on the document,
        if there is one.
        """
        old_view_id, document_id = self.views.pop(view.id)
        available_views = views_from_buffer(view.buffer_id)
        if available_views:
            new_view_id = available_views[0].id
            self.views[new_view_id] = document_id

    @filter_event
    def on_pre_save(self, view):
        """
        Save the document to temp storage, to prevent save dialogue box
        from appearing. Notify the client that the document has been saved."""

    @filter_event
    def on_post_save(self, view):
        pass

    @filter_event
    def on_modified(self, view):
        pass

    @filter_event
    def on_selection_modified(self, view):
        pass

    @filter_event
    def on_activated(self, view):
        pass

    @filter_event
    def on_deactivated(self, view):
        pass


    # Colliberation Client Events
    def message_recieved(self, message):
        """Display the message"""
        sublime.status_message(message)

    def error_recieved(self, error):
        """Display the error."""
        sublime.error_message(error)

    def document_opened(self, document):
        """ Open the document. 
        Open a window and display the document object'
        content.
        """
        sublime.active_window().open_file(document.url)

    def document_closed(self, document):
        """
        Ask the user whether or not to close the document.
        """
        sublime.status_message("Closing document.")

    def document_opened(self, document):
        pass

    def document_closed(self, document):
        pass

    def document_added(self, document):
        pass

    def document_deleted(self, document):
        pass

    def document_saved(self, document):
        pass

    def name_modified(self, document):
        pass

    def text_modified(self, document):
        pass

    def metadata_modified(self, document):
        pass

    def version_modified(self, document):
        pass


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
