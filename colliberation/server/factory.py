from twisted.internet.task import LoopingCall
'''from bravo_plugin import retrieve_named_plugins'''

from twisted.internet.protocol import ServerFactory

from colliberation.server.protocol import CollabServerProtocol
from colliberation.packets import make_packet


SAVE_FREQUENCY = 60


class CollabServerFactory(ServerFactory):

    """ A factory for server protocols
    Creates and manages connections to collaboration clients
    """

    def __init__(self, protocol_hooks=None):
        print('Starting collaboration server factory.')

        self.protocols = {}
        self.available_docs = {}
        self.save_loop = LoopingCall(self.save_all_docs)

        if protocol_hooks is not None:
            self.hooks = protocol_hooks
        else:
            self.hooks = {}

    def startFactory(self):
        print('Factory started')
        self.save_loop.start(SAVE_FREQUENCY)

    def stopFactory(self):
        print('Factory stopped')
        self.save_loop.stop()

    def broadcast(self, packet):
        for protocol in self.protocols.itervalues():
            protocol.transport.write(packet)

    def save_all_docs(self):
        self_broadcast = self.broadcast
        for document_id, document in self.available_docs.iteritems():
            document.save()
            packet = make_packet(
                'document_saved',
                document_id=document_id,
                version=document.version
            )
            self_broadcast(packet)

    def buildProtocol(self, addr):
        print('{0} is connecting...'.format(str(addr)))

        protocol = CollabServerProtocol(
            factory=self, address=addr, **self.hooks)
        protocol.available_docs = self.available_docs

        self.protocols[addr] = protocol
        return protocol
