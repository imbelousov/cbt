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

        Prefix p_ means received data from peer.
        Postfix _b means raw bytes array.

        Bitfield message reports pieces are available
        for download from this peer.

        Bitfield format:
            <1 + bitfield_len (4 bytes)>
            <5 (1 byte)>
            <bitfield>

        """
        protocol = "BitTorrent protocol"
        buf = "".join((
            chr(len(protocol)),
            protocol,
            convert.uint_chr(0, 8),
            self.info_hash,
            self.my_id
        ))
        self.send(buf)
        p_pstr_len_b = self.recv(1)
        p_pstr_len = convert.uint_ord(p_pstr_len_b)
        if p_pstr_len != len(protocol):
            raise IOError("Unknown protocol")
        p_pstr = self.recv(p_pstr_len)
        if p_pstr != protocol:
            raise IOError("Unknown protocol")
        self.recv(8)
        p_info_hash = self.recv(20)
        if p_info_hash != self.info_hash:
            raise IOError("Torrents are not the same")
        p_id = self.recv(20)
        self.id = p_id
        self.active = True
        try:
            p_bitfieldlen_b = self.recv(4)
        except:
            return
        p_bitfield_len = convert.uint_ord(p_bitfieldlen_b) - 1
        p_mid_b = self.recv(1)
        p_mid = convert.uint_ord(p_mid_b)
        if p_mid != 5:
            raise IOError("Unknown protocol")
        p_payload = self.conn.recv(p_bitfield_len)
        self.bitfield = []
        for byte in p_payload:
            byte = convert.uint_ord(byte)
            mask = 0x80
            for i in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                self.bitfield.append(bit)
        p_bitfield_miss = p_bitfield_len*8 - len(self.bitfield)
        for i in xrange(p_bitfield_miss):
            self.bitfield.append(False)

    def choke(self):
        data = None

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
