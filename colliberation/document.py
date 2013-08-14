from zope.interface import implements

from colliberation.interfaces import IDocument

from diff_match_patch import diff_match_patch as DMP

from copy import deepcopy

dmp = DMP()


class Document(object):

    """
    A shared document meant for modification from multiple sources.
    Supports basic and advanced text manipulation, including text
    insertion, deletion, diffing, patching, etc.
    """
    implements(IDocument)

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.content = kwargs.get('content', '')
        self.version = kwargs.get('version', 0)
        self.url = kwargs.get('url', '')
        self.metadata = kwargs.get('metadata', dict())

    def __eq__(self, other):
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
        self.content = (self.content[:start] +
                        text +
                        self.content[end:]
                        )

    def delete_text(self, start, end):
        self.content = (self.content[:start] +
                        self.content[end:]
                        )

    def diff(self, text, dmp=dmp):
        """
        Generates list of diffs from the documents content against
        the given text.
        """
        diffs = dmp.main_diff(self.content, text)
        return diffs

    def make_patches(self, text, dmp=dmp):
        """ Makes a series of patches against the given text.

        Diffs the given text with the document's content, and transforms
        the diff into a series of patches.
        """
        data = dmp.diff_main(self.content, text)
        data = dmp.patch_make(self.content, data)
        return data

    def patch(self, patches, dmp=dmp):
        new_content, results = dmp.patch_apply(patches, self)
        if len(results) != 0:
            print("Patch results: {}".format(results))
        return results

    def update(self, document):
        """ Updates this document to match the other document
        """
        self.name = document.name
        self.content = document.content
        self.version = document.version
        self.url = document.url
        self.metadata = document.metadata
