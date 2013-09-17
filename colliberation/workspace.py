from zope.interface import implements
from colliberation.interfaces import IWorkspace
from itertools import ifilter, islice, imap, repeat
import operator


class Workspace(object):
    implements(IWorkspace)

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.id = kwargs.get('id', 0)
        self.metadata = kwargs.get('metadata', {})
        self.documents = kwargs.get('documents', {})

    def add_document(self, document):
        self.documents[document.id] = document

    def remove_document(self, document_id):
        del(self.documents[document_id])

    def retrieve_document(self, document_id):
        return self.documents[document_id]

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

# Common key function for finding documents


def with_attributes(**attributes):
    """ Generate a function attribute-matching generator

    Constructs a generator which evaluates what objects in a given container
    have attributes with values matching the ones specified.

    Arguments
        attributes: Keyword parameters specifying attribute names and values.
    """
    # Note, container type of 'values' MUST equal container type
    # returned by 'get_attributes'
    keys = tuple(attributes.iterkeys())
    values = tuple(attributes.itervalues())
    get_attributes = operator.attrgetter(*keys)

    fill_values = repeat(values)

    def match(documents):
        doc_attributes = imap(get_attributes, documents)
        result_iterable = imap(operator.eq, doc_attributes, fill_values)
        for result in result_iterable:
            yield result

    return match
