from colliberation.server.factory import CollabServerFactory


class ColliberationServer(object):

    def __init__(self):
        self.factory = CollabServerFactory()

    def start(self, address, port):
        """
        Start listening at the given address using the given port.
        """

    def stop(self, address, port):
        """
        Stop the server.
        """
