from unittest import TestCase
from colliberation.interfaces import IWorkspace
from colliberation.workspace import Workspace
from colliberation.document import Document
from mock import Mock
from zope.interface.verify import verifyClass, verifyObject

WORKSPACE_NAME = 'Test Workspace'
WORKSPACE_ID = 46
WORKSPACE_METADATA = {'temp': True, 'prefix': 'test'}

MOCK_DOCUMENT = Mock(spec=Document())


class WorkspaceTest(TestCase):

    def setUp(self):
        self.workspace = Workspace(
            id=WORKSPACE_ID,
            name=WORKSPACE_NAME,
            metadata=WORKSPACE_METADATA
        )

    def tearDown(self):
        self.workspace = None

    def test_workspace_initialization(self):
        assertEqual = self.assertEqual
        workspace = self.workspace

        assertEqual(workspace.name, WORKSPACE_NAME)
        assertEqual(workspace.id, WORKSPACE_ID)
        assertEqual(workspace.metadata, WORKSPACE_METADATA)
        #assertEqual(workspace.documents, {})

    def test_workspace_interface_conformance(self):
        self.assertTrue(verifyClass(IWorkspace, Workspace))
        self.assertTrue(verifyObject(IWorkspace, self.workspace))

    def test_workspace_search(self):
        """
        Populate workspace with documents
        Search for documents
        Match given results to expected results.
        """
        self.fail("Not Implemented")

    def test_workspace_add_remove(self):
        """
        Add document to workspace.
        Check for document existence
        Remove Document from workspace
        Check for Document non-existence
        """
        assertTrue = self.assertTrue
        document_id = MOCK_DOCUMENT.id
        workspace = self.workspace

        workspace.add_document(MOCK_DOCUMENT)
        results = workspace.search(document_id=document_id)
        assertTrue(len(results) == 1)
        assertTrue(results[1] == MOCK_DOCUMENT)

        workspace.remove_document(MOCK_DOCUMENT)
        results = workspace.search(document_id=document_id)
        assertTrue(len(results) == 0)

    def test_workspace_remove_invalid_document(self):
        """
        Remove document from workspace.
        Check for error
        """
        self.assertRaises(
            KeyError,
            self.workspace.remove_document,
            id=20
        )

    def test_workspace_save(self):
        """
        Call function
        """
        self.workspace.save()

    def test_workspace_load(self):
        """
        Call function
        """
        self.workspace.load()
