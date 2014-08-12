#! /usr/bin/python

import time
import socket

import convert

__all__ = ["Peer"]

class Peer(object):
    def __init__(self, ip, port, info_hash, my_id):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.my_id = my_id
        self.id = ""
        self.choked = True
        self.interested = False
        self.am_choked = True
        self.am_interested = False
        self.active = False
        self.timestamp = 0
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)
        self.bitfield = []

    def connect(self):
        """Try to connect to the peer and shake hands
        or close the connection."""
        try:
            self.conn.connect((self.ip, self.port))
            self.handshake()
        except:
            self.close()

    def close(self):
        """Close the connection and make peer inactive."""
        self.conn.close()
        self.active = False

    def handshake(self):
        """The first message transmitted by client.

        Format:
            <pstr length (1 byte)>
            <pstr>
            <8 zeros (reserved)>
            <sha1 meta["info"] hash (20 bytes)>
            <my peer_id (20 bytes)>

        BitTorrent v1.0 pstr is "BitTorrent protocol".

        Bitfield message reports pieces are available
        for download from this peer.

        Bitfield format:
            <1 + bitfield_len (4 bytes)>
            <5 (1 byte)>
            <bitfield>

        """
        protocol = "BitTorrent protocol"
        # Send hello string
        buf = "".join((
            chr(len(protocol)),
            protocol,
            convert.uint_chr(0, 8),
            self.info_hash,
            self.my_id
        ))
        self.send(buf)
        # Get and check length of peer protocol string
        buf = self.recv(1)
        pstr_len = convert.uint_ord(buf)
        if pstr_len != len(protocol):
            raise IOError("Unknown protocol")
        # Get and check peer protocol string
        pstr = self.recv(pstr_len)
        if pstr != protocol:
            raise IOError("Unknown protocol")
        # Reserved bytes
        self.recv(8)
        # Get and check info hash
        info_hash = self.recv(20)
        if info_hash != self.info_hash:
            raise IOError("Torrents are not the same")
        # Get and save peer id
        id = self.recv(20)
        self.id = id
        # Toggle connection status to active
        self.active = True
        # Try to get bitfield message length
        try:
            buf = self.recv(4)
        except:
            return
        bitfield_len = convert.uint_ord(buf) - 1
        # Get message id (5 for bitfield message)
        buf = self.recv(1)
        message_id = convert.uint_ord(buf)
        if message_id != 5:
            raise IOError("Unknown protocol")
        # Get bitfield and fill a list of bits
        bitfield = self.conn.recv(bitfield_len)
        self.bitfield = []
        for byte in bitfield:
            byte = convert.uint_ord(byte)
            mask = 0x80
            for _ in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                self.bitfield.append(bit)
        bitfield_miss = bitfield_len*8 - len(self.bitfield)
        for _ in xrange(bitfield_miss):
            self.bitfield.append(False)

    def read_bitfield(self, buf, length):
        """Read raw bitfield data and fill bitfield list.
        
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

    """def choke(self):
        \"""Block this peer by client.\"""
        if self.choked:
            return
        buf = "".join((
            convert.uint_chr(1, 4),
            convert.uint_chr(0, 1)
        ))
        self.choked = True
        self.send(buf)
        self.read_response()

    def unchoke(self):
        \"""Unblock this peer by client.\"""
        if not self.choked:
            return
        buf = "".join((
            convert.uint_chr(1, 4),
            convert.uint_chr(1, 1)
        ))
        self.choked = False
        self.send(buf)
        self.read_response()"""

    def read_response(self):
        result = False
        try:
            buf = self.recv(4)
            message_len = convert.uint_ord(buf)
            if message_len == 0:
                #Todo: keep alive
                pass
            buf = self.recv(1)
            message_type = convert.uint_ord(buf)
            buf = self.conn.recv(message_len - 1)
            switch = {
                5: self.message_bitfield
            }
            if message_type in switch:
                switch[message_type](buf, message_len - 1)
        except:
            pass
        return result

    """    def get_piece(self, index, begin, length):
        data = "".join((
            convert.uint_chr(13, 4),
            convert.uint_chr(6, 1),
            convert.uint_chr(index, 4),
            convert.uint_chr(begin, 4),
            convert.uint_chr(length, 4)
        ))
        self.send(data)
        p_mlen_b = self.recv(4)
        p_mlen = convert.uint_ord(p_mlen_b)
        p_mid_b = self.recv(p_mlen)
        p_mid = convert.uint_ord(p_mid_b)
        print p_mid"""

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
