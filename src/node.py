import socket


class Buf(object):
    def __init__(self):
        self.buf = []
        self.length = 0
        self.bad_length = 0

    def append(self, string):
        self.buf.append(string)
        self.length += len(string)

    def clear(self):
        self.buf = []
        self.length = 0

    def bad(self):
        self.bad_length = self.length


class Node(object):
    MAX_CHUNK_SIZE = 1024

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.conn = None
        self.inbox = Buf()
        self.outbox = []
        self.handshaked = False
        self.bitfield = []
        self.id = ""
        self.closed = False

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)
        self.conn.connect((self.ip, self.port))
        self.conn.setblocking(False)

    def close(self):
        self.conn.close()
        self.conn = None
        self.closed = True

    def send(self, buf):
        chunks = []
        for x in xrange(0, len(buf), Node.MAX_CHUNK_SIZE):
            chunks.append(buf[x:x+Node.MAX_CHUNK_SIZE])
        self.outbox += chunks
