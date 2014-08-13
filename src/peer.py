#! /usr/bin/python

"""
Public methods:

    connect()
        Set connection with peer, exchange greetings,
        get bit mask of available for download pieces.
        Set "active" flag.
        Supports "lazy bitfield"

    c_handshake()
        Send greetings to the peer.

    p_handshake()
        Handle greetings from the peer.

    response()
        Receive, interpret and handle all commands
        sent by peer.

    is_available(piece)
        Check if peer has piece with this index.

    set_choked(bool)
        Set/reset "client choked" flag and tell peer about it.

    set_interested(bool)
        Set/reset "client interested" flag and tell peer about it.

    close()
        Close the connection with peer and reset "active" flag.
    
"""

import time
import socket

import convert

__all__ = ["Peer"]

class Peer(object):

    # -------------------------------------------------------------------------
    # Public

    def __init__(self, ip, port, info_hash, id):
        """
        c_ - client property
        p_ - peer property

        """
        self.c_id = id
        self.c_info_hash = info_hash
        self.c_choked = True
        self.c_interested = False
        self.p_ip = ip
        self.p_port = port
        self.p_id = ""
        self.p_info_hash = ""
        self.p_choked = True
        self.p_interested = False
        self.bitfield = []
        self.active = False
        self.timestamp = 0
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)
        self.protocol = "BitTorrent protocol"

    def connect(self):
        """Set connection with peer, exchange greetings,
        get bit mask of available for download pieces.
        Set "active" flag.
        
        """
        self._connect()

    def c_handshake(self):
        """Send greetings to the peer."""
        self._write_handshake()

    def p_handshake(self):
        """Handle greetings from the peer."""
        self._read_handshake()

    def response(self):
        """Receive, interpret and handle all commands
        sent by peer.
        
        """
        self._read_all()

    def is_available(self, piece):
        """Check if peer has piece with this index."""
        return (
            len(self.bitfield) > piece
            and self.bitfield[piece]
            and self.active
        )

    def set_choked(self, value):
        """Set/reset "peer choked" flag and tell peer about it."""
        if value:
            self._write_choke()
        else:
            self._write_unchoke()

    def set_interested(self, value):
        """Set/reset "peer interested" flag and tell peer about it."""
        if value:
            self._write_interested()
        else:
            self._write_notinterested()

    def close():
        """Close the connection with peer and reset "active" flag."""
        self._close()

    # -------------------------------------------------------------------------
    # Private

    def _connect(self):
        try:
            self.conn.connect((self.p_ip, self.p_port))
            self._write_handshake()
            self._read_handshake()
            self.active = True
        except IOError, e:
            self._close()
            return
        self._read_all()

    def _close(self):
        self.conn.close()
        self.active = False
        self.bitfield = []

    def _read_handshake(self):
        """The first message transmitted by peer."""
        # Get and check length of peer protocol string
        buf = self._recv(1)
        pstr_len = convert.uint_ord(buf)
        if pstr_len != len(self.protocol):
            raise IOError("Unknown protocol")
        # Get and check peer protocol string
        pstr = self._recv(pstr_len)
        if pstr != self.protocol:
            raise IOError("Unknown protocol")
        # Reserved bytes
        self._recv(8)
        # Get and check info hash
        self.p_info_hash = self._recv(20)
        if self.p_info_hash != self.c_info_hash:
            raise IOError("Torrents are not the same")
        # Get and save peer id
        self.p_id = self._recv(20)

    def _read_all(self):
        """Read all messages (from 0 to n)."""
        while True:
            try:
                self._read_message()
            except IOError, e:
                break

    def _read_message(self):
        """Detect message type and call appropriate handler."""
        buf = self._recv(4)
        message_len = convert.uint_ord(buf)
        if message_len == 0:
            # Keep-alive message
            return
        buf = self._recv(1)
        message_type = convert.uint_ord(buf)
        buf = self._recv(message_len - 1)
        switch = {
            0: self._read_choke,
            1: self._read_unchoke,
            2: self._read_interested,
            3: self._read_notinterested,
            4: self._read_have,
            5: self._read_bitfield
        }
        if message_type in switch:
            switch[message_type](buf, message_len - 1)

    def _read_choke(self, buf, length):
        """Handler for "choke" command."""
        if length != 1:
            self._close()
        self.p_choked = True

    def _read_unchoke(self, buf, length):
        """Handler for "unchoke" command."""
        if length != 1:
            self._close()
        self.p_choked = False

    def _read_interested(self, buf, length):
        """Handler for "interested" command."""
        if length != 1:
            self._close()
        self.p_interested = True

    def _read_notinterested(self, buf, length):
        """Handler for "not interested" command."""
        if length != 1:
            self._close()
        self.p_interested = False

    def _read_have(self, buf, length):
        """Handler for "have" command.
        
        "Have" message indicates that some piece becomes
        ready to download from the peer.
        
        """
        if length != 4:
            self._close()
        index = convert.uint_ord(buf)
        if index < len(self.bitfield):
            self.bitfield[index] = True

    def _read_bitfield(self, buf, length):
        """Handler for "bitfield" command. Fills bitfield list.
        
        "Bitfield" message represents which pieces are ready
        to download from the peer.
        
        """
        self.bitfield = []
        for byte in buf:
            byte = convert.uint_ord(byte)
            mask = 0x80
            for _ in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                self.bitfield.append(bit)

    def _write_handshake(self):
        """The first message transmitted by client."""
        buf = "".join((
            chr(len(self.protocol)),    # Length of protocol string
            self.protocol,              # Protocol string
            convert.uint_chr(0, 8),     # Reserved bytes
            self.c_info_hash,           # Client info hash (20 bytes)
            self.c_id                   # Client ID (20 bytes)
        ))
        self._send(buf)

    def _write_keepalive(self):
        """Client need to send this if it hasn't communicated with peer in last 2 minutes."""
        buf = convert.uint_chr(0, 4)
        self._send(buf)

    def _write_choke(self):
        buf = "".join((
            convert.uint_chr(1, 4),   # Message length
            convert.uint_chr(0, 1)    # Message type
        ))
        self._send(buf)
        self.c_choked = True
        self._read_all()

    def _write_unchoke(self):
        buf = "".join((
            convert.uint_chr(1, 4),   # Message length
            convert.uint_chr(1, 1)    # Message type
        ))
        self._send(buf)
        self.c_choked = False
        self._read_all()

    def _write_interested(self):
        buf = "".join((
            convert.uint_chr(1, 4),   # Message length
            convert.uint_chr(2, 1)    # Message type
        ))
        self._send(buf)
        self.c_interested = True
        self._read_all()

    def _write_notinterested(self):
        buf = "".join((
            convert.uint_chr(1, 4),   # Message length
            convert.uint_chr(3, 1)    # Message type
        ))
        self._send(buf)
        self.c_interested = False
        self._read_all()

    def _send(self, bytes):
        """Send bytes to peer and remember the time when it happened."""
        self.conn.sendall(bytes)
        self.timestamp = time.time()

    def _recv(self, length):
        """Try to receive n bytes from peer ; remember the time if it was successful."""
        bytes = ""
        while len(bytes) != length:
            try:
                buf = self.conn.recv(length - len(bytes))
                bytes = "".join((bytes, buf))
            except socket.timeout:
                buf = ""
            if len(buf) == 0:
                raise IOError("End of stream")
        self.timestamp = time.time()
        return bytes
