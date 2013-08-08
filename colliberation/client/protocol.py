from colliberation.protocol import CollaborationProtocol
from colliberation.packets import make_packet

from diff_match_patch import diff_match_patch as DMP

from twisted.internet.task import LoopingCall

from warnings import warn

dmp = DMP()
PING_RATE = 55
USERNAME = 'user'
WAITING_FOR_AUTH = 1
AUTHORIZED = 2

class CollabClientProtocol(CollaborationProtocol):

    """ A generic colliberation client protocol.

    A colliberation client protocol mostly acts on orders from the server, only
    acting when it gets appropriate messages from the server, even if the
    orders are in reaction to a message it sent originally.
    """


    # Utilities

    _warn_doc_not_available = 'Document ID {} not in available_docs'.format
    _warn_doc_not_found = 'Document ID {} not in open_docs'.format
