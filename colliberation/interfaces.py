"""
Interfaces defining base components required by colliberation.
"""
from zope.interface import Interface, Attribute
from bravo_plugin import IBravoPlugin, ISortedPlugin


class IDocument(Interface):

    """ A shared document being edited by multiple people.

    An object implementing IDocument represents a text based file supporting
    advanced text manipulation techniques and multi-versioning.
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
        should remain unchanged outside of .

        """)

    content = Attribute(""" The document's content.""")

    version = Attribute(""" The version number of the document.""")

    url = Attribute(""" File url of the document.""")

    metadata = Attribute(""" The document's metadata.

        A document's metadata is a dictionary-like object containing the
        object's metadata. Data should be of basic, easily serialized types.

        """)

    def insert_text(position, text, version):
        """ Insert text into the document.

        Inserts the given text into the document's content at the specified
        position. The given version specifies what version of document the text
        should be inserted into.

        :param int position: Position to insert the text at in the document.
        :param str text: Text to insert into the document.
        :param str version: Version of the document to insert the text into.
        """

    def delete_text(position, text, version):
        """ Delete text from the document.

        Deletes the given text from the document's content at the specified
        position. The given version specifies what version of document the text
        should be inserted into.

        :param int position: Position to insert the text at in the document.
        :param str text: Text to insert into the document.
        :param str version: Version of the document to insert the text into.
        """

    def commit():
        """ Commit any pending operations to the document's content.

        Commits any unprocessed operations to the document's content, possibly
        changing the document's version in the process.
        """

    def revert(version):
        """ Revert the document's state to the specified version.

        Reverts the document's state to the given version raising
        NoSuchVersion if the given document version cannot be found or used.

        :param int version: Version of the document to revert to.
            Raises NoSuchVersion if the version specified cannot be found.
        """

    def available_versions():
        """ Retrieve a list of available versions of this document.

        :returns: Returns a list of versions available to the document.
            Any version on this list should be safe to use with rollback
        """

    def retrieve_version_data(version):
        """ Retrieves data associated with the document at that version.

        Returns a dictionary containing document data for the given version.
        Raises NoSuchVersion if the specified version cannot be found or
        accessed.

        :param int version: Version of the document to retrieve data from.
            Raises NoSuchVersion if the version specified cannot be found.
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


class IDocOpenedHook(IBravoPlugin):

    def document_opened(protocol, document):
        """ Interface for plugins interested in requests to open a document.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocClosedHook(IBravoPlugin):

    def document_closed(protocol, document):
        """ Interface for plugins interested in requests to close a document.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocSavedHook(IBravoPlugin):

    def document_saved(protocol, document):
        """ Interface for plugins interested in document save requests.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocAddedHook(IBravoPlugin):

    def document_added(protocol, document):
        """ Interface for plugins interested in document creation requests.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """


class IDocDeletedHook(IBravoPlugin):

    def document_deleted(protocol, document):
        """ Interface for plugins interested in document deletion requests.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        """

document_hooks = {}

# Document data event hooks


class ITextChangedHook(IBravoPlugin):

    def text_changed(protocol, document, changes):
        """ Interface for plugins interested in requests to change
        a document's content.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        :param str changes: A string representing the changes meant
            for the document
        """


class INameChangedHook(IBravoPlugin):

    def name_changed(protocol, document, new_name):
        """ Interface for plugins interested in requests to change a
        document's name.

        :param CollaborationProtocol protocol: The protocol requesting
            the name change.
        :param Document document: The document the request refers to.
        :param str new_name: The new name for the document.
        """


class IMetadataChangedHook(IBravoPlugin):

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


class IVersionChangedHook(IBravoPlugin):

    def version_changed(protocol, document, new_version):
        """ Interface for plugins interested in requests to change a
        document's version.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param Document document: The document the request refers to.
        :param int new_version: The new version of the document.
        """

# Misc event hooks


class IMessageHook(IBravoPlugin):

    def message_recieved(protocol, message):
        """ Interface for plugins interested in protocol messages.

        :param CollaborationProtocol protocol: The protocol requesting
            the text change.
        :param str message: The message from the protocol.
        """


class IErrorHook(IBravoPlugin):

    def error_recieved(protocol, error_type, message):
        """ Interface for plugins interested in protocol error messages.

        :param CollaborationProtocol protocol: The protocol requesting
            sending the error message.
        :param int error_type: The error type.
        :param str message: The error message.
        """
misc_hooks = {}
