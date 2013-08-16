#!/user/bin/python27

import os
import sys
# Hack to allow us to import external libraries
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from colliberation.server.factory import CollabServerFactory
from colliberation.packets import make_packet
from twisted.manhole.telnet import ShellFactory

prof = None

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
    server_factory = CollabServerFactory()
    shell_factory = ShellFactory()

    server_endpoint = TCP4ServerEndpoint(reactor, port)

    shell_factory.username = ""
    shell_factory.password = ""

    def get_client():
        for i in server_factory.protocols:
            return server_factory.protocols[i]

    def run_packets():
        c = get_client()
        c.document_added(add_packet)
        c.document_opened(open_packet)
        c.text_modified(text_mod_packet)
    shell_factory.namespace['get_client'] = get_client
    shell_factory.namespace['runp'] = run_packets
    shell_factory.namespace['factory'] = server_factory

    server_connection = server_endpoint.listen(server_factory)
    shell_connection = reactor.listenTCP(6684, shell_factory)
    reactor.run()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        print(traceback.format_exc())
        raw_input()
    else:
        import time
        time.sleep(30)
