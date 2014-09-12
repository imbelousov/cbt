import socket
import struct
import sys
import time
sys.path.insert(0, "..")

import base
import buffer
import event


class BitTorrentPeer(base.BasePeer):
    CHUNK = 1 << 10
    KEEP_ALIVE = 100
    PROTOCOL = "BitTorrent protocol"
    TIMEOUT = 120

    MESSAGE_CHOKE = 0
    MESSAGE_UNCHOKE = 1
    MESSAGE_INTERESTED = 2
    MESSAGE_NOTINTERESTED = 3
    MESSAGE_HAVE = 4
    MESSAGE_BITFIELD = 5
    MESSAGE_REQUEST = 6
    MESSAGE_PIECE = 7
    MESSAGE_CANCEL = 8

    SPECIAL_WAIT_UNCHOKE = 1

    def __init__(self, ip, port, my_id, info_hash):
        super(BitTorrentPeer, self).__init__(ip, port)
        self._conn = None
        self._client_id = my_id
        self._client_info_hash = info_hash
        self._inbox = buffer.Buffer()
        self._last_recv = 0
        self._last_send = 0
        self._message_expected = False
        self._outbox = []

        self.bitfield = []
        self.client_choke = True
        self.client_interested = False
        self.handshaked = False
        self.id = None
        self.peer_choke = True
        self.peer_interested = False

        self.on_close = event.Event()
        self.on_have = event.Event()
        self.on_piece = event.Event()

    def connect(self):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.settimeout(2)
        try:
            self._conn.connect((self.ip, self.port))
            self._conn.setblocking(False)
        except (socket.error, socket.timeout):
            self.close()

    def close(self):
        try:
            self._conn.close()
            self.on_close()
        except (socket.error, AttributeError):
            pass
        self._conn = None

    def poll(self):
        def recv():
            chunk = ""
            try:
                chunk = self._conn.recv(BitTorrentPeer.CHUNK)
                self._last_recv = time.time()
            except socket.error as err:
                if err.errno != 10035:
                    raise
            if chunk:
                self._inbox.push(chunk)

        def send():
            if len(self._outbox):
                message = self._outbox[0]
                if message == BitTorrentPeer.SPECIAL_WAIT_UNCHOKE:
                    if not self.peer_choke:
                        del self._outbox[0]
                else:
                    del self._outbox[0]
                    for x in xrange(0, len(message), BitTorrentPeer.CHUNK):
                        chunk = message[x:x+BitTorrentPeer.CHUNK]
                        self._conn.send(chunk)
                        self._last_send = time.time()
            elif time.time() - self._last_send >= BitTorrentPeer.KEEP_ALIVE:
                self._outbox.append(struct.pack(">I", 0))

        if not self._conn:
            return

        try:
            send()
            recv()
            self._read_command()
        except socket.error:
            self.close()

    def request(self, index, begin, length):
        if self.peer_choke:
            self.send_message_unchoke()
            self.send_message_interested()
            self.wait_unchoke()
        self.send_message_request(index, begin, length)

    def _handle_message(self, message):
        """Read a single message that received from the peer.
        Format: llll[t][p...p]
        l - length of message (0 if it's a keep-alive)
        t - type of message
        p - payload of message

        """
        if not len(message):
            # Keep-alive
            return
        message_type = ord(message[0])
        message_payload = message[1:]
        switch = {
            BitTorrentPeer.MESSAGE_CHOKE: self._handle_message_choke,
            BitTorrentPeer.MESSAGE_UNCHOKE: self._handle_message_unchoke,
            BitTorrentPeer.MESSAGE_INTERESTED: self._handle_message_interested,
            BitTorrentPeer.MESSAGE_NOTINTERESTED: self._handle_message_notinterested,
            BitTorrentPeer.MESSAGE_HAVE: self._handle_message_have,
            BitTorrentPeer.MESSAGE_BITFIELD: self._handle_message_bitfield,
        }
        if message_type not in switch:
            # Unsupported message
            return
        handler = switch[message_type]
        handler(message_payload)

    def _send_message(self, type_, payload):
        buf = [
            struct.pack(">I", len(payload) + 1),
            chr(type_),
            payload
        ]
        self._outbox.append("".join(buf))

    def _handle_message_choke(self, payload):
        if len(payload):
            # Invalid message
            self.close()
            return
        self.peer_choke = True

    def send_message_choke(self):
        self._send_message(BitTorrentPeer.MESSAGE_CHOKE, "")
        self.client_choke = True

    def _handle_message_unchoke(self, payload):
        if len(payload):
            # Invalid message
            self.close()
            return
        self.peer_choke = True

    def send_message_unchoke(self):
        self._send_message(BitTorrentPeer.MESSAGE_UNCHOKE, "")
        self.client_choke = False

    def _handle_message_interested(self, payload):
        if len(payload):
            # Invalid message
            self.close()
            return
        self.peer_interested = True

    def send_message_interested(self):
        self._send_message(BitTorrentPeer.MESSAGE_INTERESTED, "")
        self.client_interested = True

    def _handle_message_notinterested(self, payload):
        if len(payload):
            # Invalid message
            self.close()
            return
        self.peer_interested = False

    def send_message_notinterested(self):
        self._send_message(BitTorrentPeer.MESSAGE_NOTINTERESTED, "")
        self.client_interested = False

    def _handle_message_have(self, payload):
        if len(payload) != 4:
            # Invalid message
            self.close()
            return
        index = struct.unpack(">I", payload)[0]
        if len(self.bitfield) <= index:
            self.bitfield += [False] * (index - len(self.bitfield) + 1)
        self.bitfield[index] = True
        self.on_have()

    def _handle_message_bitfield(self, payload):
        self.bitfield = []
        for byte in payload:
            mask = 0x80
            byte = ord(byte)
            for _ in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                self.bitfield.append(bit)
        self.on_have()

    def send_message_request(self, index, begin, length):
        payload = struct.pack(">III", index, begin, length)
        self._send_message(BitTorrentPeer.MESSAGE_REQUEST, payload)

    def send_handshake(self):
        buf = [
            chr(len(BitTorrentPeer.PROTOCOL)),
            BitTorrentPeer.PROTOCOL,
            "\0" * 8    # Reserved bytes
            self._client_info_hash,
            self._client_id
        ]
        self._outbox.append("".join(buf))

    def wait_unchoke(self):
        self._outbox.append(BitTorrentPeer.SPECIAL_WAIT_UNCHOKE)

    def _read_command(self):
        if not len(self._inbox):
            return

        if not self.handshaked:
            # Read the first message in a conversation
            if len(self._inbox) < 49 + len(BitTorrentPeer.PROTOCOL):
                return
            protocol_id_length_bytes = self._inbox.pull(1)
            protocol_id_length = ord(protocol_id_length_bytes)
            if protocol_id_length != len(BitTorrentPeer.PROTOCOL):
                self.close()
                return
            protocol_id = self._inbox.pull(protocol_id_length)
            if protocol_id != BitTorrentPeer.PROTOCOL:
                self.close()
                return
            # Reserved 8 bytes - write code here to expand BitTorrent protocol
            reserved = self._inbox.pull(8)
            peer_info_hash = self._inbox.pull(20)
            if peer_info_hash != self._client_info_hash:
                self.close()
                return
            peer_id = self._inbox.pull(20)
            self.id = peer_id
            self.handshaked = True

        if self._message_expected is False:
            # Start to listen a message
            if len(self._inbox) < 4:
                return
            message_length_bytes = self._inbox.pull(4)
            message_length = struct.unpack(">I", message_length_bytes)[0]
            self._message_expected = message_length

        # I am waiting for a message
        if len(self._inbox) < self._message_expected:
            return
        message = self._inbox.pull(self._message_expected)
        self._handle_message(message)
        self._message_expected = False
