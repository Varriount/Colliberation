from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from colliberation.client.protocol import CollabClientProtocol


class CollabClientFactory(ReconnectingClientFactory):

    """
    A factory which produces collaboration clients.
    """

    nextid = 0
    client_class = CollabClientProtocol

    def __init__(self):
        self.protocols = {}
        self.deferreds = {}

    def connect_to_server(self, address, port):
        """ Connect to a server. """
        reactor.connectTCP(address, port, self)
        deferred = Deferred()
        self.deferreds[address + str(port)] = deferred
        return deferred

    def buildProtocol(self, destination):
        protocol = self.client_class()
        protocol.factory = self
        key = destination.host + str(destination.port)
        self.protocols[key] = protocol

        deferred = self.deferreds[key]
        deferred.callback(protocol)
        return protocol
