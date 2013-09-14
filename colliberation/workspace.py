from zope.interface import implements
from colliberation.interfaces import IWorkspace
from itertools import ifilter, islice


class Workspace(object):
    implements(IWorkspace)

    def __init__(self, name, id, metadata):
        self.name = name
        self.id = id
        self.metadata = metadata
        self.documents = {}

    def add_document(self, document):
        self.documents[document.id] = document

    def remove_document(self, document_id):
        del(self.documents[document_id])

    def search_for_documents(self, filter_func, max_results=None):
        iterable = islice(
            ifilter(filter_func, self.documents.itervalues()),
            0, max_results
        )
        return iterable

    def save(self):
        pass

    def load(self):
        pass
