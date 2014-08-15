import socket
import time

class Peer(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.id = None
        self.active = False
        self.p_choked = True
        self.c_choked = True
        self.p_interested = False
        self.c_interested = False
        self.bitfield = []
        self.timestamp = 0
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)

    def connect(self):
        self.conn.connect((self.ip, self.port))
        self.active = True

    def close(self):
        self.conn.close()
        self.active = False

    def set_id(self, id):
        self.id = id

    def get_id(self, id_):
        assert self.id is not None
        return self.id

    def send(self, bytes):
        """Remembers when was the last communication."""
        assert self.active
        self.conn.sendall(bytes)
        self.timestamp = time.time()

    def recv(self, size):
        """Sometimes socket doesn't read all bytes in one iteration.
        This solves the problem.
        Remembers when was the last communication.

        """
        assert self.active
        bytes = ""
        while True:
            buf = self.conn.recv(size)
            bytes = "".join((bytes, buf))
            if len(bytes) == size or len(buf) == 0:
                break
        self.timestamp = time.time()
        return bytes
