from zope.interface import implements

from colliberation.interfaces import IDocument

from magicstring import MagicString

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
        content = kwargs.get('content', '')
        self.content = MagicString(content)
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

    def insert_text(self, position, text):
        self.content = (self.content[:position] +
                        text +
                        self.content[position:]
                        )

    def delete_text(self, position, text):
        self.content = (self.content[:position] +
                        self.content[len(text):]
                        )

    def replace_text(self, position, text):
        self.content = (self.content[:position] +
                        text +
                        self.content[len(text):]
                        )

    def diff(self, text):
        """
        Generates list of diffs from the documents content against
        the given text.
        """
        diffs = dmp.main_diff(self.content, text)
        diffs = dmp.diff_cleanupEfficiency(diffs)
        return diffs

    def make_patches(self, text):
        """ Makes a series of patches against the given text.

        Diffs the given text with the document's content, and transforms
        the diff into a series of patches.
        """
        data = dmp.main_diff(self.content, text)
        data = dmp.diff_cleanupEfficiency(data)
        data = dmp.patch_make(self.content, data)
        return data

    def patch(self, patches):
        new_content, results = dmp.patch_main(self.content, patches)
        print("Path results: {}".format(results))
        self.content = new_content
        return results
