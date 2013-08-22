from copy import deepcopy

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
        self.serializer = kwargs.get('serializer', None)

    def __eq__(self, other):
        """Comparison function.

        Child classes should usually call this function.

        :param other: Object to compare against.
        """
        if not isinstance(other, Document):
            return False
        results = (
            (self.name == other.name),
            (self.content == other.content),
            (self.version == other.version),
            (self.url == other.url),
            (self.metadata == other.metadata)
        )
        return all(results)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return self.__class__(
            name=self.name,
            content=self.content,
            version=self.version,
            url=self.url,
            metadata=self.metadata
        )

    def __deepcopy__(self, memo):
        return self.__class__(
            name=deepcopy(self.name, memo),
            content=deepcopy(self.content, memo),
            version=deepcopy(self.version, memo),
            url=deepcopy(self.url, memo),
            metadata=deepcopy(self.metadata, memo)
        )

    def change_text(self, start, text, end):
        """Change (Replace or insert) a document's content.

        This function should be called whenever a document's contents need
        to be modified, rather than changing a document's content attribute.
        This allows child classes to hook into specific text operations.

        :param int start: The start position. The position 'x' is the space
            after the x'th character in the documents content.
        :param str text: The text to insert.
        :param int end: The end position.
        """
        log(
            DOC_TEXT_CHANGE_LOG.format(start, end, text)
        )

        self.content = (self.content[:start] +
                        text +
                        self.content[end:]
                        )

    def delete_text(self, start, end):
        """Delete a section of a document's content.

        See :change_text:

        :param int start: The start position.
        :param int end: The end position.
        """
        log(
            DOC_TEXT_DELETED_LOG.format(start, end)
        )
        self.content = (self.content[:start] +
                        self.content[end:]
                        )

    def diff(self, text, dmp):
        """ Diff this document against the given text.

        Generates a list of differences from the documents content against
        the given text.

        :param str text: Text to compare against.
        :param DMP dmp: A diff match patch object.

        :returns: A list of differences
        """
        diffs = dmp.main_diff(self.content, text)
        return diffs

    def make_patches(self, text, dmp):
        """ Makes a series of patches against the given text.

        Diffs the given text with the document's content, and transforms
        the diff into a series of patches.

        :param str text: Text to compare against.
        :param DMP dmp: Diff match patch object to use.
        """
        data = dmp.diff_main(self.content, text)
        data = dmp.patch_make(self.content, data)
        return data

    def patch(self, patches, dmp):
        log(patches)
        new_content, results = dmp.patch_apply(patches, self)
        if len(results) != 0:
            log(new_content)
            log("Patch results: " + str(results))
        return results

    def update(self, document):
        """ Updates this document to match the other document.
        """
        self.name = document.name
        self.content = document.content
        self.version = document.version
        self.url = document.url
        self.metadata = document.metadata

    def open(self):
        self.state_deferral = Deferred()
        return self.state_deferral

    def close(self):
        if self.state_deferral is not None:
            self.state_deferral.callback(self)

    def save(self):
        self.serializer.save(self)
