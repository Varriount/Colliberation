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
        """ Load a document from the disk.

        Loads a pickled document object from the file located at the 
        specified URL.

        :param str url: URL Location of the pickled document.
        """
        parts = urlparse(url)
        if parts.scheme != 'file':
            raise Exception('URL {0} is not a file'.format(parts.scheme))
        path = parts.path
        with open(path, 'r') as file_handle:
            data = pickle.load(file_handle)
        return data

    def save_document(self, document):
        """Saves a document to disk.
        
        Pickles a document and, using the document's url attribute, 
        saves it to disk. 
        
        :param Document document: Document to save.
        """
        parts = urlparse(document.url)
        if parts.scheme != 'file':
            raise Exception('URL {0} is not a file'.format(parts.scheme))
        path = parts.path
        with open(path, 'w') as file_handle:
            pickle.dump(document, file_handle)

    def delete_document(self, url):
        pass
