#!/user/bin/python27
import os
import sys
# Hack to allow us to import external libraries
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from colliberation.document import Document
from colliberation.protocol import CollaborationProtocol
from colliberation.client.factory import CollabClientFactory
from colliberation.packets import make_packet
from twisted.internet import reactor
from twisted.manhole.telnet import ShellFactory
import traceback
# Colliberation client that reads from a text file periodically to update text.
# Proof of concept


class PollDocument(Document, object):

    def __init__(self, **kwargs):
        self._content = ""
        Document.__init__(self, **kwargs)
        self._content = self.content

    @property
    def content(self):
        with open(self.name + 'test.d', 'r') as fh:
            result = fh.read()
            self._content = result
        return result

    @content.setter
    def content(self, content):
        if self._content != content:
            with open(self.name + 'test.d', 'w') as fh:
                print('Writing content.')
                fh.write(content)
        return


class PollProtocol(CollaborationProtocol):
    doc_class = PollDocument


class PollFactory(CollabClientFactory):
    client_class = PollProtocol


message_packet = make_packet('message',
                             message='I am a message')

error_packet = make_packet('error',
                           error_type=5,
                           message='I am an error')

open_packet = make_packet('document_opened',
                          document_id=60,
                          version=80)

closed_packet = make_packet('document_closed',
                            document_id=60,
                            version=80)

add_packet = make_packet('document_added',
                         document_id=60,
                         version=80,
                         document_name='test.py')

delete_packet = make_packet('document_deleted',
                            document_id=60,
                            version=80)

name_mod_packet = make_packet('name_modified',
                              document_id=60,
                              version=80,
                              new_name='table.py')

text_mod_packet = make_packet('text_modified',
                              document_id=60,
                              version=80,
                              modifications='@@ -0,0 +1,7 @@\n+abcdefg\n')

metadata_mod_packet = make_packet('metadata_modified',
                                  document_id=60,
                                  version=80,
                                  type='int',
                                  key='owner',
                                  value='tester')

packets = {'metadata_mod_packet': metadata_mod_packet,
           'text_mod_packet': text_mod_packet,
           'name_mod_packet': name_mod_packet,
           'delete_packet': delete_packet,
           'open_packet': open_packet,
           'closed_packet': closed_packet,
           'add_packet': add_packet,
           'error_packet': error_packet,
           'message_packet': message_packet
           }


def main():
    port = 6687
    address = '127.0.0.1'

    collab_factory = PollFactory()
    shell_factory = ShellFactory()

    shell_factory.username = ""
    shell_factory.password = ""

    def get_client():
        for i in collab_factory.protocols:
            return collab_factory.protocols[i]

    def run_packets():
        c = get_client()
        c.transport.write(add_packet)
        c.transport.write(open_packet)
        c.transport.write(text_mod_packet)
    shell_factory.namespace['factory'] = collab_factory
    shell_factory.namespace['get_client'] = get_client
    shell_factory.namespace['runp'] = run_packets
    shell_factory.namespace.update(packets)

    collab_connection = collab_factory.connect_to_server(address, port)
    manhole_connection = reactor.listenTCP(6686, shell_factory)

    reactor.run()


try:
    main()
except Exception:
    print(traceback.format_exc())
    raw_input()
else:
    import time
    time.sleep(30)
