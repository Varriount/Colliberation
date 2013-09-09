from colliberation.interfaces import IDocument
from twisted.internet.defer import Deferred
from zope.interface import implements

DOC_TEXT_CHANGE_LOG = 'Changing document text at {0}:{1} to "{2}"'
DOC_TEXT_DELETED_LOG = 'Deleting document text at {0}:{1}'

DEBUG = True


def log(text):
    if DEBUG:
        print(text)


class Document(object):

    """
    A shared document supporting modification from multiple sources.
    Supports basic and advanced text manipulation, including text
    insertion, deletion, diffing, patching, etc.
    """
    implements(IDocument)

    state_deferral = None

    def __init__(self, **kwargs):
        """Initialize the document with the given data.

        Note that any child classes should call this method when
        initializing, unless they plan to set these attributes themselves.
        """
        self.id = kwargs.get('id', 0)
        self.name = kwargs.get('name', '')
        self.content = kwargs.get('content', '')
        self.version = kwargs.get('version', 0)
        self.url = kwargs.get('url', '')
        self.metadata = kwargs.get('metadata', dict())

    def change_text(self, start, end, text):
        """Change (Replace or insert) a document's content.

        This method should be called whenever a document's contents need
        to be modified, rather than changing a document's content attribute.
        This allows child classes to hook into specific text operations.

        Arguments:
            start (int): The start position. The position 'x' is the space
                after the x'th character in the documents content.
            text (str): The text to insert.
            end (int): The end position.
        """
        self_content = self.content

        valid_params = (0 < start < end <= len(self_content))
        if valid_params:
            log(DOC_TEXT_CHANGE_LOG.format(start, end, text))
            self.content = (self.content[:start] + text + self.content[end:])
        else:
            raise ValueError(
                'Invalid points for change. ({0}:{1})'.format(start, end)
            )

    def delete_text(self, start, end):
        """Delete a section of a document's content.

        See :meth:`change_text`

        :param int start: The start position.
        :param int end: The end position.
        """
        self_content = self.content

        valid_params = (0 < start < end <= len(self_content))
        if valid_params:
            log(DOC_TEXT_DELETED_LOG.format(start, end))
            self.content = (self_content[:start] + self_content[end:])
        else:
            raise ValueError(
                'Invalid points for deletion. ({0}:{1})'.format(start, end)
            )

    def diff(self, text, dmp):
        """ Diff this document against the given text.

        Generates a list of differences from the documents content against
        the given text.

        Arguments:
            text (str): Text to compare against.
            dmp (DMP): A diff match patch object.

        Returns:
            A list of differences.
        """
        diffs = dmp.main_diff(self.content, text)
        return diffs

    def make_patches(self, text, dmp):
        """ Makes a series of patches against the given text.

        Diffs the given text with the document's content, and transforms
        the diff into a series of patches.

        Arguments:
            text (str): Text to compare against.
            dmp (DMP): Diff match patch object to use.

        Returns:
            A list of patches.
        """
        data = dmp.diff_main(self.content, text)
        data = dmp.patch_make(self.content, data)
        return data

    def patch(self, patches, dmp):
        """ Patch the document using the given patches.

        Uses the given dmp object to apply the given patches to the
        document's contents.

        Arguments:
            patches: A list of patches to use.
            dmp (DMP): The diff match patch object to use.
        """
        log(patches)
        new_content, results = dmp.patch_apply(patches, self)
        if len(results) != 0:
            log(new_content)
            log("Patch results: " + str(results))
        return results

    def update(self, document, include_id=True):
        """ Updates this document to match the other document.

        Note:
            This updates the ID of the document. Be careful!

        Arguments:
            document (Document): Document to update to.
        """
        if include_id:
            self.id = document.id
        self.name = document.name
        self.content = document.content
        self.version = document.version
        self.url = document.url
        self.metadata = document.metadata

    def open(self):
        """ Open the document.

        This method must be called on a document before any changes or
        alterations are made. This allows the document to set up it's
        internal state at the appropriate time of use, as well as send
        a deferred which will fire upon the document being closed.

        Returns:
            defer (Deferred): A deferred object which will fire upon the
            document being closed. This allows the document to inform
            outside sources of it being closed, and allows the document
            to close itself if need be.

        """
        if not self.is_open:
            self.state_deferral = Deferred()
            self.is_open = True
            return self.state_deferral
        else:
            raise StateException(
                'Document {0} with ID {1} already open.'.format(self, self.id)
            )

    def close(self):
        """ Close the document.

        Close the document, taking care of any internal state that needs to
        be finalized. This will call the deferred responsible for notifying
        outside sources of the document's closing, if it has not already been
        called.
        """
        if self.is_open:
            if self.state_deferral is not None:
                self.state_deferral.callback(self)
            self.is_open = False
        else:
            raise StateException(
                'Document {0} with ID {1} already closed.'.format(
                    self, self.id)
            )

    def save(self, serializer=None):
        pass


class StateException(Exception):

    """
    Exception for errors caused by internal state exceptions in a document.
    Examples include already being open when open() is called, closed when
    closed() is called, etc.
    """
    pass
