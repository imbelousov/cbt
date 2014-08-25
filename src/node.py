import socket
import time


class Buf(object):
    def __init__(self):
        self.buf = []
        self.length = 0
        self.bad_length = 0

    def append(self, string):
        self.buf.append(string)
        self.length += len(string)

    def bad(self):
        self.bad_length = self.length

    def clear(self):
        self.buf = []
        self.length = 0


class Node(object):
    """Each Node object is peer in the BitTorrent network.

    Attributes:

        bitfield:
            Indicates if each piece is available for download.

        conn:
            Connection.

        c_choke:
            Client ignores the peer.

        c_interested:
            Client is going to download anything from the peer.

        handshaked:
            Is the peer ready to messaging.

        id:
            20-byte identifier in the BitTorrent network.

        inbox:
            Buffer that stores unhandled incoming messages.

        ip:
            IP address.

        last_recv:
            When the last chunk was received from the peer.

        last_send:
            When the last message was sent to the peer.

        outbox:
            Buffer that stores unsent outgoing messages.

        port:
            Incoming TCP port.

        p_choke:
            The peer ignores client.

        p_interested:
            The peer is going to download anything from client.

    """
    MAX_PART_SIZE = 1024

    def __init__(self, ip, port):
        self.bitfield = []
        self.conn = None
        self.c_choke = True
        self.c_interested = False
        self.handshaked = False
        self.id = ""
        self.inbox = Buf()
        self.ip = ip
        self.last_recv = 0
        self.last_send = 0
        self.outbox = []
        self.port = port
        self.p_choke = True
        self.p_interested = False

    def close(self):
        self.inbox = Buf()
        self.outbox = []
        self.conn.close()
        self.conn = None

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)
        self.conn.connect((self.ip, self.port))
        self.conn.setblocking(False)

    def send(self, buf):
        chunks = []
        for x in xrange(0, len(buf), Node.MAX_PART_SIZE):
            chunks.append(buf[x:x+Node.MAX_PART_SIZE])
        self.outbox += chunks

    def sleep(self, timeout):
        self.outbox.append(int(time.time() + timeout))
