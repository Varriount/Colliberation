# Colliberation client that reads from a text file periodically to update text.
from colliberation.document import Document
from colliberation.protocol import CollaborationProtocol


class PollDocument(Document, object):

    def __init__(self, **kwargs):
        Document.__init__(self, **kwargs)

    @property
    def content(self):
        with open(self.name, 'r') as fh:
            print('Reading content.')
            result = fh.read()
        return result

    @content.setter
    def content(self, content):
        with open(self.name, 'w') as fh:
            print('Writing content.')
            fh.write(content)
        return


class PollProtocol(CollaborationProtocol):
    doc_class = PollDocument
