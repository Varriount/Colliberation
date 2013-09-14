"""
Interfaces defining base components required by colliberation.
"""
from zope.interface import Interface, Attribute


class IWorkspace(Interface):

    """ A collection of shared documents.

    A workspace holds and manages data concerning a group of documents.
    """

    name = Attribute("Name of the workspace. May change during runtime.")
    id = Attribute("Workspace ID. Must not change during runtime.")
    metadata = Attribute("Dict-like object containing workspace metadata.")

    def add_document(document):
        """ Add the given document to the workspace.

        :param Document document: The document object to add
        """

    def remove_document(document_id):
        """ Remove the given document from the workspace.

        :param int document_id: The id of the document to remove.
        """

    def search_for_documents(filter_func, max_results=0):
        """ Search for a number of documents using a filter function.

        Searches for documents within the workspace for which the given filter
        function indicates is true, returning at most the number of results
        specified by max_results

        The filter function will be called repeatedly with lists of documents
        to search through. The filter function should return, each time it is
        called, a list of True/False values corresponding to each document.

        Since such a search may take significant amount of time, long enough to
        block, an iterable/generator should be returned which will produce the
        next search result each iteration. Each iteration should take as little
        time as possible to return the next result.

        :param function filter_func: The function to use to filter documents.
        :param int max_results: Maximum number of results to return. A value
        less than 0 indicates that all results should be returned.

        :returns: An iterable/generator containing the results.
        """

    def save():
        """ Signals that the workspace will be saved.

        This will be called by a serializer or other object before saving the
        workspace, in order to notify the workspace that it is going to be
        saved.
        """

    def load():
        """
        Signals that this workspace will be loaded.

        This method will be called to indicate that the workspace is
        about to be loaded.
        """


class IDocument(Interface):

    """ A shared document being edited by multiple people.

    An object implementing IDocument represents a text based file supporting
    text manipulation.
    """

    id = Attribute(""" Internal document ID.

        A document's id is used to internally reference the document, as
        it should never change during runtime. The document id may still
        change from runtime to runtime though.
        :type: int
        """)

    name = Attribute(""" Name of the document.

        A document's name is used as a human-friendly identifier for the
        document, as well as a label that the document may be referenced by
        when being saved and loaded from persistant storage. Unlike a
        document's id, a documents name may change during runtime, however it
        should remain unchanged while in persistant storage.

        """)

    content = Attribute(""" The document's content.""")

    version = Attribute(""" The version number of the document.""")

    url = Attribute(""" File url of the document.""")

    metadata = Attribute(""" The document's metadata.

        A document's metadata is a dictionary-like object containing the
        object's metadata. Data should be of basic, easily serialized types.

        """)

    def change_text(start, end, text):
        """ Insert or replace text into the document.

        Inserts or replaces the given text into the document's content at the
        specified position.

        :param int start: Position to insert the text at in the document.
        :param str text: Text to insert into the document.
        """

    def delete_text(start, end):
        """ Delete text from the document.

        Deletes the given text from the document's content at the specified
        position. The given version specifies what version of document the text
        should be inserted into.

        :param int start: Start position of region to delete.
        :param int end: End position of region to delete.
        """

    def open():
        """ 'Open' the document.

        Signal to the document that it should prepare itself for being read
        and written to. Returns a deferred that may be fired by the document
        itself in order to signal to outside sources that it should be closed.

        :returns: A deferred.
        """

    def close():
        """ 'Close' the document.

        Note:
            A document should never call its own close method. If the document
            internals must close the document, they should fire the deferred.

        Signal to the document that it should commit any changes and wrap up
        any internal state, before becoming inactive.
        """

    def save():
        """ Signal to the document to save.

        Signal to the document that it is going to be saved to persistant
        storage. This should be called by any serializer that wishes to save
        the document, in order to notify the document that it is being saved.
        """

    def update(document):
        """ Update the document to match the given document.

        Updates this document's internals to match the given document's
        internals.

        Note:
            This function should /never/ change the document's own ID.

        :param Document document: The document to update to.
        """


class IDocumentSerializer(Interface):

    """ Serializer for objects implementing IDocument.

    An IDocumentSerializer is responsible for loading, deleting, and saving
    objects implementing IDocument.
    """

    def load_document(url):
        """ Load a document from persistant storage.

        :param str url: A url identifying the document resource.
        """

    def save_document(document):
        """ Save a document to persitant storage.

        :param Document document: A document to save.
        """

    def delete_document(url):
        """ Delete a document from persistant storage.

        :param str url: A url identifying the document resource.
        """

# Event Hooks
event_hooks = {}  # Updated below, after each section of plugins

# Document event hooks


class IDocOpenedHook(Interface):

    def document_opened(protocol, document):
        """ Interface for plugins interested in requests to open a document.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocClosedHook(Interface):

    def document_closed(protocol, document):
        """ Interface for plugins interested in requests to close a document.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocSavedHook(Interface):

    def document_saved(protocol, document):
        """ Interface for plugins interested in document save requests.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocAddedHook(Interface):

    def document_added(protocol, document):
        """ Interface for plugins interested in document creation requests.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocDeletedHook(Interface):

    def document_deleted(protocol, document):
        """ Interface for plugins interested in document deletion requests.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """

document_hooks = {}

# Document data event hooks


class ITextChangedHook(Interface):

    def text_changed(protocol, document, changes):
        """ Interface for plugins interested in requests to change
        a document's content.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        :param str changes: A string representing the changes meant
            for the document
        """


class INameChangedHook(Interface):

    def name_changed(protocol, document, new_name):
        """ Interface for plugins interested in requests to change a
        document's name.

        :param CollaborationProtocol protocol: The protocol requesting
            the name change.
        :param Document document: The document the request refers to.
        :param str new_name: The new name for the document.
        """


class IMetadataChangedHook(Interface):

    def metadata_changed(protocol, document, type, key, value):
        """ Interface for plugins interested in requests to change
        a document's metadata.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        :param str type: The type of the key.
        :param str key: The metadata key.
        :param str value: The value for the key.
        """


class IVersionChangedHook(Interface):

    def version_changed(protocol, document, new_version):
        """ Interface for plugins interested in requests to change a
        document's version.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        :param int new_version: The new version of the document.
        """

# Misc event hooks


class IMessageHook(Interface):

    def message_recieved(protocol, message):
        """ Interface for plugins interested in protocol messages.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param str message: The message from the protocol.
        """


class IErrorHook(Interface):

    def error_recieved(protocol, error_type, message):
        """ Interface for plugins interested in protocol error messages.

        :param CollaborationProtocol protocol: The protocol requesting
            sending the error message.
        :param int error_type: The error type.
        :param str message: The error message.
        """
misc_hooks = {}
