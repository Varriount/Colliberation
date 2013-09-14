"""
Collaboration server protocol tests.
"""
from unittest import TestCase
from colliberation.tests.utils import FakeTransport, generate_packets
from twisted.internet.task import LoopingCall
from colliberation.protocol import (CollaborationProtocol,
                                    WAITING_FOR_AUTH, AUTHORIZED)
from mock import MagicMock


class CollaborationProtocolTest(TestCase):

    def setUp(self):
        self.transport = FakeTransport()
        self.protocol = CollaborationProtocol()
        self.protocol.transport = self.transport
        self.packets = generate_packets()

    def test_init(self):
        self.assertEqual(self.protocol.open_docs, {})
        self.assertEqual(self.protocol.available_docs, {})
        self.assertEqual(self.protocol.state, WAITING_FOR_AUTH)

        self.assertEqual(self.protocol.username, '')
        self.assertEqual(self.protocol.ping_loop, None)

    def test_connectionMade(self):
        self.protocol.connectionMade()
        self.assertIsInstance(self.protocol.ping_loop, LoopingCall)

    def test_handshake_recieved(self):
        self.protocol.handshake_recieved(self.packets['handshake_packet'])
        self.assertEqual(self.protocol.state, AUTHORIZED)
        # self.assertEqual(self.protocol.other_name,
        # self.packets['handshake_packet'].name)

    def test_message_recieved(self):
        self.protocol.message_recieved(self.packets['message_packet'])

    def test_error_recieved(self):
        self.assertRaises(UserWarning, self.protocol.error_recieved,
                          self.packets['error_packet'])

    def test_document_opened(self):
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])

        self.get_opened_doc()

    def test_document_closed(self):
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])
        self.protocol.document_closed(self.packets['closed_packet'])

        self.get_available_doc()
        self.assertRaises(KeyError, self.get_opened_doc)

    def test_document_saved(self):
        self.protocol.serializer = MagicMock(spec=self.protocol.serializer)
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])
        self.protocol.document_saved(self.packets['save_packet'])

    def test_document_added(self):
        self.protocol.document_added(self.packets['add_packet'])

    def test_document_deleted(self):
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])
        self.protocol.document_deleted(self.packets['delete_packet'])

        self.assertRaises(KeyError, self.get_opened_doc)
        self.assertRaises(KeyError, self.get_available_doc)

    def test_name_modified(self):
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])
        self.protocol.name_modified(self.packets['name_mod_packet'])

        document = self.get_opened_doc()
        self.assertEqual(document.name, self.packets['document_newname'])

    """
    def test_text_modified(self):
            with patch('colliberation.protocol.dmp', autospec=True) as mocker:
                mock
                self.protocol.document_added(self.packets['add_packet'])
                self.protocol.document_opened(self.packets['open_packet'])
                self.protocol.text_modified(self.packets['text_mod_packet'])
    """

    def test_metadata_modified(self):
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])
        self.protocol.metadata_modified(self.packets['metadata_mod_packet'])

        # document = self.get_opened_doc()
        # self.assertEqual(document, self.packets[version])

    def test_version_modified(self):
        self.protocol.document_added(self.packets['add_packet'])
        self.protocol.document_opened(self.packets['open_packet'])
        self.protocol.version_modified(self.packets['version_mod_packet'])

        document = self.get_opened_doc()
        self.assertEqual(document.version, self.packets['version'])

    def get_opened_doc(self):
        return self.protocol.open_docs[self.packets['document_id']]

    def get_available_doc(self):
        return self.protocol.available_docs[self.packets['document_id']]
