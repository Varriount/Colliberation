from colliberation.client.factory import CollabClientFactory
from colliberation.sublime.protocol import SublimeCollabProtocol

from sublime_utils import current_view


class SublimeClientFactory(CollabClientFactory):
    client_class = SublimeCollabProtocol

    def __init__(self, hook):
        CollabClientFactory.__init__(self)
        self.hook = hook

    def startedConnecting(self, connector):
        current_view().set_status(
            'Collaboration',
            'Started Connecting at {0}...'.format(connector))
        self.hook.startedConnecting(connector)

    def clientConnectionFailed(self, connector, reason):
        current_view().set_status(
            'Collaboration',
            'Connection failed at {0} - ({1})'.format(connector, reason)
        )
        self.hook.clientConnectionFailed(connector, reason)

    def clientConnectionLost(self, connector, reason):
        current_view().set_status(
            'Collaboration',
            'Connection lost at {0} - ({1})'.format(connector, reason))

        self.hook.clientConnectionLost(connector, reason)

        destination = connector.getDestination()
        key = destination.host + str(destination.port)
        del(self.protocols[key])

    def startFactory(self):
        print('Factory started')

    def stopFactory(self):
        print('Factory stopped')
