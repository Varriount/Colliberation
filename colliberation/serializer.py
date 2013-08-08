import pickle
from zope.interface import implements
from colliberation.interfaces import IDocumentSerializer
from urlparse import urlparse


class DiskSerializer(object):

    """
    A simple file based document serializer which saves document objects to
    disk using python's pickle module.
    """
    implements(IDocumentSerializer)

    def load_document(self, url):
        parts = urlparse(url)
        if parts.scheme != 'file':
            raise Exception('URL {0} is not a file'.format(parts.scheme))
        path = parts.path
        with open(path, 'r') as file_handle:
            data = pickle.load(file_handle)
        return data

    def save_document(self, document):
        parts = urlparse(document.url)
        if parts.scheme != 'file':
            raise Exception('URL {0} is not a file'.format(parts.scheme))
        path = parts.path
        with open(path, 'w') as file_handle:
            pickle.dump(document, file_handle)

    def delete_document(self, url):
        pass
