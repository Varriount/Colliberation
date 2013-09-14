"""Serializer tests
Initializing Serializer
Loading a document
Saving a document
Deleting a document
"""
from tempfile import mkdtemp
from shutil import rmtree
from colliberation.document import Document
from colliberation.serializer import DiskSerializer
from urllib import pathname2url
from unittest import TestCase
import pickle


class Serializer_Test(TestCase):

    def setUp(self):
        self.folder = mkdtemp()
        self.path = self.folder + '\\test.py'
        self.url = "file:" + pathname2url(
            self.path).replace('\\', '/').strip('///')
        self.data = Document(name='test.py',
                             content='hello world',
                             version=6,
                             url=self.url,
                             metadata={
                             'owner': 'foo',
                             'date': 11306, },
                             serializer=None)
        self.serializer = DiskSerializer()

    def tearDown(self):
        self.serializer = None
        rmtree(self.folder)

    def test_load(self):
        file = open(self.path, 'w')
        pickle.dump(self.data, file)
        file.close()
        data = self.serializer.load_document(self.url)


        self.assertEqual(
            data, self.data, 'Loaded data did not match test data.')

    def test_save_load(self):
        self.serializer.save_document(self.data)
        data = self.serializer.load_document(self.data.url)
        self.assertEqual(data, self.data)

    def test_delete(self):
        pass
