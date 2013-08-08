from colliberation.document import Document
from unittest import TestCase

TEST_NAME = 'testDoc'
TEST_ID = 42
TEST_VERSION = 0
TEST_URL = 'file:\\\test.py'
TEST_DATA = {'Owner': 'tester'}
TEST_CONTENT = 'A quick red fox jumped over the brown lazy dog.'
TEST_INSERTION_TEXT = 'yogurt'


class DocumentInitTest(TestCase):

    def test_document_init(self):
        d = Document(name=TEST_NAME, content=TEST_CONTENT,
                     version=TEST_VERSION, url=TEST_URL, metadata=TEST_DATA)
        self.assertEqual(d.version, TEST_VERSION)
        self.assertEqual(d.url, TEST_URL)
        self.assertEqual(d.metadata, TEST_DATA)
        self.assertEqual(d.content, TEST_CONTENT)


class DocumentTest(TestCase):

    def setUp(self):
        self.document = Document(name=TEST_NAME, content=TEST_CONTENT,
                                 version=TEST_VERSION, url=TEST_URL,
                                 metadata=TEST_DATA)

    def tearDown(self):
        self.document = None

    def test_insert_text(self):
        pass
        # self.document.insert(TEST_INSERTION_TEXT)

    def test_delete_text(self):
        pass

    def test_commit(self):
        pass

    def test_revert(self):
        pass

    def test_available_versions(self):
        pass

    def test_retrieve_version_data(self):
        pass
