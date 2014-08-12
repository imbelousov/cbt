#! /usr/bin/python

"""
    
"""

import time
import socket

import convert

__all__ = ["Peer"]

class Peer(object):
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
        self.conn.settimeout(5)
        self.protocol = "BitTorrent protocol"

    def connect(self):
        """Try to connect to the peer or close the connection."""
        try:
            self.conn.connect((self.p_ip, self.p_port))
            self.send_handshake()
            self.recv_handshake()
            self.active = True
        except:
            self.close()
        try:
            self.read_response()
        except:
            pass

    def close(self):
        """Close the connection and make peer inactive."""
        self.conn.close()
        self.active = False

    def send_handshake(self):
        """The first message transmitted by client."""
        buf = "".join((
            chr(len(self.protocol)),    # Length of protocol string
            self.protocol,              # Protocol string
            convert.uint_chr(0, 8),     # Reserved bytes
            self.c_info_hash,           # Client info hash (20 bytes)
            self.c_id                   # Client ID (20 bytes)
        ))
        self.send(buf)

    def recv_handshake(self):
        """The first message transmitted by peer."""
        # Get and check length of peer protocol string
        buf = self.recv(1)
        pstr_len = convert.uint_ord(buf)
        if pstr_len != len(self.protocol):
            raise IOError("Unknown protocol")
        # Get and check peer protocol string
        pstr = self.recv(pstr_len)
        if pstr != self.protocol:
            raise IOError("Unknown protocol")
        # Reserved bytes
        self.recv(8)
        # Get and check info hash
        self.p_info_hash = self.recv(20)
        if self.p_info_hash != self.c_info_hash:
            raise IOError("Torrents are not the same")
        # Get and save peer id
        self.p_id = self.recv(20)

    def read_response(self):
        """Detect message type and call appropriate handler."""
        buf = self.recv(4)
        message_len = convert.uint_ord(buf)
        if message_len == 0:
            #Todo: keep alive
            pass
        buf = self.recv(1)
        message_type = convert.uint_ord(buf)
        buf = self.conn.recv(message_len - 1)
        switch = {
            0: self.read_choke,
            1: self.read_unchoke,
            2: self.read_interested,
            3: self.read_notinterested,
            5: self.read_bitfield
        }
        if message_type in switch:
            switch[message_type](buf, message_len - 1)

    def read_choke(self, buf, length):
        if length != 1:
            self.close()
        self.c_choked = True

    def read_unchoke(self, buf, length):
        if length != 1:
            self.close()
        self.c_choked = False

    def read_interested(self, buf, length):
        if length != 1:
            self.close()
        self.c_interested = True

    def read_notinterested(self, buf, length):
        if length != 1:
            self.close()
        self.c_interested = False

    def read_bitfield(self, buf, length):
        """Handle raw bitfield data and fill bitfield list.
        
        Bitfield message represents which pieces are ready to download from the peer.
        """
        self.bitfield = []
        for byte in buf:
            byte = convert.uint_ord(byte)
            mask = 0x80
            for _ in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                self.bitfield.append(bit)
        missed = (length - len(buf))*8
        for _ in xrange(missed):
            self.bitfield.append(False)

    def write_choke(self):
        buf = "".join((
            convert.uint_chr(1, 4),    # Message length
            convert.uint_chr(0, 1)     # Message type
        ))
        self.send(buf)
        self.p_choked = True

    def write_unchoke(self):
        buf = "".join((
            convert.uint_chr(1, 4),    # Message length
            convert.uint_chr(1, 1)     # Message type
        ))
        self.send(buf)
        self.p_choked = False

    def write_interested(self):
        buf = "".join((
            convert.uint_chr(1, 4),    # Message length
            convert.uint_chr(2, 1)     # Message type
        ))
        self.send(buf)
        self.p_interested = True

    def write_notinterested(self):
        buf = "".join((
            convert.uint_chr(1, 4),    # Message length
            convert.uint_chr(3, 1)     # Message type
        ))
        self.send(buf)
        self.p_interested = False

    def send(self, bytes):
        """Send bytes to peer and remember the time when it happened."""
        self.conn.sendall(bytes)
        self.timestamp = time.time()

    def recv(self, length):
        """Try to receive n bytes from peer ; remember the time if it was successful."""
        bytes = self.conn.recv(length)
        if len(bytes) != length:
            raise IOError("End of stream")
        self.timestamp = time.time()
        return bytes
