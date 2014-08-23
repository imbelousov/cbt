import socket


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
    MAX_CHUNK_SIZE = 1024

    def __init__(self, ip, port):
        """
        Peer attributes:
            bitfield: indicates if each piece is available for download
            conn: connection
            handshaked: is the peer ready to messaging
            id: 20-byte identifier in BitTorrent network
            inbox: buffer that stores unhandled incoming messages
            ip: IP address
            last_recv: when the last chunk was received from the peer
            last_send: when the last message was sent to the peer
            outbox: buffer that stores unsent outgoing messages
            port: incoming TCP port

        """
        self.bitfield = []
        self.conn = None
        self.handshaked = False
        self.id = ""
        self.inbox = Buf()
        self.ip = ip
        self.last_recv = 0
        self.last_send = 0
        self.outbox = []
        self.port = port

    def close(self):
        self.conn.close()
        self.conn = None

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)
        self.conn.connect((self.ip, self.port))
        self.conn.setblocking(False)

    def send(self, buf):
        chunks = []
        for x in xrange(0, len(buf), Node.MAX_CHUNK_SIZE):
            chunks.append(buf[x:x+Node.MAX_CHUNK_SIZE])
        self.outbox += chunks
