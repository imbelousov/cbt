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

    Methods:

        close():
            Close the connection to the peer and clear buffers.

        connect():
            Try to connect to the peer in CONNECTION_TIMEOUT seconds.

        send(data):
            Put the data in the outbox buffer queue. The data will be
            divided into pieces of MAX_PART_SIZE bytes or less.

        sleep(timeout):
            Suspend sending of next messages for a <timeout> seconds.

        wait_for_unchoke():
            Suspend sending of next messages until the peer
            chokes the client.

    """

    CONNECTION_TIMEOUT = 2
    MAX_PART_SIZE = 1024

    MESSAGE_WAITING_UNCHOKING = -1

    FALSE = 0
    WAITING = 1
    TRUE = 2

    def __init__(self, ip, port):
        self.active = 0
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
        self.p_choke = Node.TRUE
        self.p_interested = False

    def close(self):
        """Close the connection to the peer and clear buffers."""
        self.inbox = Buf()
        self.outbox = []
        self.conn.close()
        self.conn = None

    def connect(self):
        """Try to connect to the peer in CONNECTION_TIMEOUT seconds."""
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(Node.CONNECTION_TIMEOUT)
        self.conn.connect((self.ip, self.port))
        self.conn.setblocking(False)

    def get_piece(self, index):
        """Return True if the peer has the piece."""
        if 0 <= index < len(self.bitfield):
            return self.bitfield[index]
        else:
            return False

    def set_piece(self, index, have=True):
        """Remember that the peer has the piece."""
        if index < 0:
            return
        b_len = len(self.bitfield)
        if index >= b_len:
            for _ in xrange(index - b_len + 1):
                self.bitfield.append(False)
        self.bitfield[index] = have

    def send(self, data):
        """Put the data in the outbox buffer queue. The data will be
        divided into pieces of MAX_PART_SIZE bytes or less.

        """
        chunks = []
        for x in xrange(0, len(data), Node.MAX_PART_SIZE):
            chunks.append(data[x:x+Node.MAX_PART_SIZE])
        self.outbox += chunks

    def sleep(self, timeout):
        """Suspend sending of next messages for a <timeout> seconds.
        Notice: time is counted from the current time, so
            node.sleep(2)
            node.send("Foo")
            node.sleep(2)
            node.send("bar")
        will send "Foobar" instantly after 2 seconds. You need to use this:
            node.sleep(2)
            node.send("Foo")
            node.sleep(4)
            node.send("bar")

        """
        self.outbox.append(int(time.time() + timeout))

    def wait_for_unchoke(self):
        """Suspend sending of next messages until the peer
        chokes the client.

        """
        self.outbox.append(Node.MESSAGE_WAITING_UNCHOKING)
