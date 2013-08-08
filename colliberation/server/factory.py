from weakref import WeakValueDictionary
'''from bravo_plugin import retrieve_named_plugins'''

from twisted.internet.protocol import ServerFactory

from colliberation.server.protocol import CollabServerProtocol


class CollabServerFactory(ServerFactory):

    """ A factory for server protocols
    Creates and manages connections to collaboration clients
    """

    def __init__(self, protocol_hooks=None):
        print('Starting collaboration server factory.')

        self.protocols = WeakValueDictionary()
        self.available_documents = {}

        if protocol_hooks is not None:
            self.hooks = protocol_hooks
        else:
            self.hooks = {}

    def startFactory(self):
        print('Factory started')

    def stopFactory(self):
        print('Factory stopped')

    def broadcast(self, packet):
        for proto in self.protocols.itervalues():
            proto.transport.write(packet)

    def buildProtocol(self, addr):
        print('{0} is connecting...'.format(str(addr)))

        protocol = CollabServerProtocol(
            factory=self, address=addr, **self.hooks)

        self.protocols[addr] = protocol
        return protocol
