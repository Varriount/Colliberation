from construct import Struct, Container
from construct import Embed, Switch, OptionalGreedyRange
from construct import UBInt32, UBInt8, PascalString
"""
Packets for the collaboration protocol.
Overall layout/design, as well as most functions, are based on
MostAwesomeDude's bravo project's packets.py
"""

DUMP_ALL_PACKETS = False
# Helper structures
document_action = Struct('document_action',
                         UBInt32('document_id'),
                         UBInt32('version')
                         )

# Utility Action Packets
#: Handshake - TODO - Use some form of authentication
"""
handshake = Struct('handshake',
                   PascalString('username'),
                   UBInt32('ping_rate')
                   )
"""

handshake = Struct('handshake',
                   PascalString('username')
                   )

ping = Struct('ping')

# A regular message
message = Struct('message',
                 PascalString("message")
                 )

#: An error message
error_packet = Struct('error',
                      UBInt32('error_type'),
                      PascalString('message')
                      )


# Document Action Packets

#: Signals that a document has been (or should be) opened.
document_opened = Struct('document_opened',
                         Embed(document_action)
                         )

#: Signals that a document has been (or should be) closed
document_closed = Struct('document_closed',
                         Embed(document_action)
                         )

#: Signals that a document has been (or should be) saved
document_saved = Struct('document_saved',
                        Embed(document_action)
                        )

#: Signals that a document has been (or should be) deleted.
document_deleted = Struct('document_deleted',
                          Embed(document_action)
                          )

#: Signals that a document has been added to the list of available documents
document_added = Struct('document_added',
                        Embed(document_action),
                        PascalString("document_name")
                        )

#: Signals that a document has been renamed
name_modified = Struct('name_modified',
                       Embed(document_action),
                       PascalString('new_name')
                       )

# Document Content Action Packets

#: Signals that text has been modified
text_modified = Struct('text_modified',
                       Embed(document_action),
                       PascalString('modifications'),
                       PascalString('hash')
                       )

#: Signals that document metadata has changed.
metadata_modified = Struct('metadata_modified',
                           Embed(document_action),
                           PascalString('type'),
                           PascalString('key'),
                           PascalString('value'),
                           )

version_modified = Struct('version_modified',
                          Embed(document_action),
                          UBInt32('new_version')
                          )


#: Packet Header definitions
packets = {
    #: Utility Action Packets
    0: ping,
    4: handshake,
    5: message,
    6: error_packet,

    #: Document Action Packets
    10: document_opened,
    11: document_closed,
    12: document_saved,
    13: document_added,
    14: document_deleted,
    15: name_modified,

    #: Document Content Action Packets
    20: text_modified,
    21: metadata_modified,
    22: version_modified
}

#: Packets by name
packets_by_name = dict((v.name, k) for (k, v) in packets.iteritems())


#: Packet streams
packet_stream = Struct("packet_stream",
                       OptionalGreedyRange(
                       Struct("packet",
                              UBInt8("header"),
                              Switch("payload", lambda context: context[
                                     "header"], packets),
                              ),
                       ),
                       OptionalGreedyRange(
                       UBInt8("leftovers"),
                       ),
                       )

# Parsing functions


def parse_packets(bytestream):
    """
    Opportunistically parse out as many packets as possible from a raw
    bytestream.

    Returns a tuple containing a list of unpacked packet containers, and any
    leftover unparseable bytes.
    """

    container = packet_stream.parse(bytestream)

    l = [(i.header, i.payload) for i in container.packet]
    leftovers = "".join(chr(i) for i in container.leftovers)

    if DUMP_ALL_PACKETS:
        for packet in l:
            print "Parsed packet %d" % packet[0]
            print packet[1]

    return l, leftovers


def parse_packets_incrementally(bytestream):
    """
    Parse out packets one-by-one, yielding a tuple of packet header and packet
    payload.

    This function returns a generator.

    This function will yield all valid packets in the bytestream up to the
    first invalid packet.

    :returns: a generator yielding tuples of headers and payloads
    """

    while bytestream:
        parsed = packet_stream.parse(bytestream)
        header = parsed.full_packet.header
        payload = parsed.full_packet.payload
        bytestream = "".join(chr(i) for i in parsed.leftovers)

        yield header, payload


def make_packet(packet, *args, **kwargs):
    """
    Constructs a packet bytestream from a packet header and payload.

    The payload should be passed as keyword arguments. Additional containers
    or dictionaries to be added to the payload may be passed positionally, as
    well.
    """

    if packet not in packets_by_name:
        print "Couldn't find packet name %s!" % packet
        return ""

    header = packets_by_name[packet]

    for arg in args:
        kwargs.update(dict(arg))
    container = Container(**kwargs)

    if DUMP_ALL_PACKETS:
        print "Making packet %s (%d)" % (packet, header)
        print container
    try:
        payload = packets[header].build(container)
    except AttributeError:
        print('Parameter not specified!')
        raise
    return chr(header) + payload
