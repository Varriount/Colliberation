from colliberation.document import Document, StateException
from colliberation.interfaces import IDocument
from zope.interface.verify import verifyClass, verifyObject
from unittest import TestCase
from mock import Mock

# Testing Parameters
DOC_NAME = 'testDoc'
DOC_ID = 42
DOC_VERSION = 0
DOC_URL = 'file:\\\test.py'
DOC_DATA = {'Owner': 'tester'}
DOC_CONTENT = 'A quick red fox jumped over the brown lazy dog.'

CHANGED_CONTENT = 'A yogurt red fox jumped over the brown lazy dog.'
CHANGED_TEXT = 'yogurt'
DELETED_CONTENT = 'A  red fox jumped over the brown lazy dog.'

TEXT_START, TEXT_END = 2, 7
INVALID_POSITIONS = (
    (-3, TEXT_END),
    (TEXT_START, 400),
    (TEXT_END, TEXT_START)
)

SERIALIZER = Mock()
UPDATE_DATA = Mock()
UPDATE_DATA.configure_mock(
    name=DOC_NAME,
    id=DOC_ID,
    version=DOC_VERSION,
    url=DOC_URL,
    metadata=DOC_DATA,
    content=DOC_CONTENT
)


class DocumentTest(TestCase):

    def setUp(self):
        self.document = Document(
            id=DOC_ID,
            name=DOC_NAME,
            content=DOC_CONTENT,
            version=DOC_VERSION,
            url=DOC_URL,
            metadata=DOC_DATA,
        )

    def tearDown(self):
        self.document = None

    def test_doc_interface_conformance(self):
        """
        Test that the document class we're testing conforms to the protocol.
        """
        self.assertTrue(verifyClass(IDocument, Document))
        self.assertTrue(verifyObject(IDocument, self.document))

    def test_change_text(self):
        """
        Test changing the document's content.
        """
        self.document.open()
        self.document.change_text(
            TEXT_START,
            TEXT_END,
            CHANGED_TEXT,
        )
        self.document.close()
        self.assertNotEqual(self.document.content, DOC_CONTENT)
        self.assertEqual(self.document.content, CHANGED_CONTENT)

    def test_document_init(self):
        """
        Test that the document initializes correctly.
        """
        d = self.document
        self.assertEqual(d.id, DOC_ID)
        self.assertEqual(d.name, DOC_NAME)
        self.assertEqual(d.content, DOC_CONTENT)
        self.assertEqual(d.version, DOC_VERSION)
        self.assertEqual(d.url, DOC_URL)
        self.assertEqual(d.metadata, DOC_DATA)

    def test_change_invalid_text(self):
        """
        Test rejection of invalid parameters when changing document text.
        """
        self.document.open()
        for start, end in INVALID_POSITIONS:
            self.assertRaises(
                ValueError,
                self.document.change_text,
                start,
                end,
                CHANGED_TEXT,
            )
            self.assertEqual(self.document.content, DOC_CONTENT)
        self.document.close()

    def test_delete_text(self):
        """
        Test deletion of a document's content.
        """
        self.document.open()
        self.document.delete_text(
            TEXT_START,
            TEXT_END
        )
        self.document.close()
        self.assertNotEqual(self.document.content, DOC_CONTENT)
        self.assertEqual(self.document.content, DELETED_CONTENT)

    def test_delete_invalid_text(self):
        """
        Test rejection of invalid parameters when deleting document text.
        """
        self.document.open()
        for start, end in INVALID_POSITIONS:
            self.assertRaises(
                ValueError,
                self.document.delete_text,
                start,
                end
            )
            self.assertEqual(self.document.content, DOC_CONTENT)
        self.document.close()

    def test_document_open(self):
        """
        Test that a document opens correctly
        """
        self.document.open()

    def test_document_double_open(self):
        """
        Test rejection of multiple opens
        """
        self.document.open()
        self.assertRaises(StateException, self.document.open)

    def test_document_close(self):
        """
        Test that a document closes correctly.
        """
        self.document.open()
        self.document.close()

    def test_document_double_close(self):
        """
        Test that a document rejects attempts to close multiple times.
        """
        self.assertRaises(StateException, self.document.close)
        self.document.open()
        self.document.close()
        self.assertRaises(StateException, self.document.close)

    def test_document_save(self):
        """
        Test that a document saves correctly.
        Since this only notifies the document that it is being saved
        (And the standard document doesn't need to do anything when saved)
        This just calls the document's save function to make sure that it runs
        without error.
        """
        self.document.save()

    def test_document_update(self):
        """
        Test that a document updates correctly.
        Make a mock name
        """
        self.document.update(UPDATE_DATA, include_id=True)
        d = self.document

        self.assertEqual(d.id, UPDATE_DATA.id)
        self.assertEqual(d.name, UPDATE_DATA.name)
        self.assertEqual(d.content, UPDATE_DATA.content)
        self.assertEqual(d.version, UPDATE_DATA.version)
        self.assertEqual(d.url, UPDATE_DATA.url)
        self.assertEqual(d.metadata, UPDATE_DATA.metadata)
