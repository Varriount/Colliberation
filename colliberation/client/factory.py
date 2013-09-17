from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from colliberation.protocol import CollaborationProtocol


class CollabClientFactory(ReconnectingClientFactory):

    """
    A factory which produces collaboration clients.
    """

    nextid = 0
    client_class = CollaborationProtocol

    def __init__(self):
        self.protocols = dict()
        self.temp = {}

    def connect_to_server(self, address, port):
        """ Connect to a server. """

        connector = reactor.connectTCP(address, port, self)
        destination = connector.getDestination()
        defer = Deferred()
        self.temp[destination.host + str(destination.port)] = defer
        return defer

    def startedConnecting(self, connector):
        print('Started Connecting at {0}...'.format(str(connector)))

    def startFactory(self):
        print('Factory started')

    def stopFactory(self):
        print('Factory stopped')

    def buildProtocol(self, address):
        print('Connecting to {0}...'.format(str(address)))

        protocol = self.client_class()
        protocol.factory = self
        protocol.address = address
        signature = address.host + str(address.port)

        self.protocols[signature] = protocol
        return protocol
