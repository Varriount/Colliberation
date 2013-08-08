"""
Testings utility objects.
"""
from random import randint
from mock import MagicMock
import os


class FakeTransport(object):

    data = []
    lost = False

    def write(self, data):
        self.data.append(data)

    def loseConnection(self):
        self.lost = True


def generate_packets():
    doc_id = randint(0, 255)
    ver = randint(0, 255)
    mess = os.urandom(randint(0, 80))
    err = os.urandom(randint(0, 80))
    err_type = randint(0, 255)
    user = 'user'
    doc_name = os.urandom(randint(0, 80)) + '.' + os.urandom(randint(0, 3))
    doc_newname = os.urandom(randint(0, 80)) + '.' + os.urandom(randint(0, 3))
    packets = {
        'document_id': doc_id,

        'version': ver,

        'message': mess,

        'error': err,

        'error_type': err_type,

        'username': user,

        'document_name': doc_name,

        'document_newname': doc_newname,

        'handshake_packet': MagicMock('handshake',
                                      username=user),

        'message_packet': MagicMock('message',
                                    message=mess),

        'error_packet': MagicMock('error',
                                  error_type=err_type,
                                  message=err),

        'open_packet': MagicMock('document_opened',
                                 document_id=doc_id,
                                 version=ver),

        'save_packet': MagicMock('document_saved',
                                 document_id=doc_id,
                                 version=ver),

        'closed_packet': MagicMock('document_closed',
                                   document_id=doc_id,
                                   version=ver),

        'add_packet': MagicMock('document_added',
                                document_id=doc_id,
                                version=ver,
                                document_name=doc_name),

        'delete_packet': MagicMock('document_deleted',
                                   document_id=doc_id,
                                   version=ver),

        'name_mod_packet': MagicMock('name_modified',
                                     document_id=doc_id,
                                     version=ver,
                                     new_name=doc_newname),

        'text_mod_packet': MagicMock('text_modified',
                                     document_id=doc_id,
                                     version=ver,
                                     modifications=''),

        'metadata_mod_packet': MagicMock('metadata_modified',
                                         document_id=doc_id,
                                         version=ver,
                                         type='int',
                                         key='owner',
                                         value='tester'),

        'version_mod_packet': MagicMock('version_modified',
                                        document_id=doc_id,
                                        version=ver,
                                        new_version=ver + 1)
    }
    return packets
