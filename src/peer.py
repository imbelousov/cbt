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
        self.conn.settimeout(3)
        self.bitfield = []

    def connect(self):
        try:
            self.conn.connect((self.ip, self.port))
            self.handshake()
        except:
            self.close()

    def close(self):
        self.conn.close()
        self.active = False

    def handshake(self):
        protocol = "BitTorrent protocol"
        data = "".join((
            chr(len(protocol)),
            protocol,
            convert.uint_chr(0, 8),
            self.info_hash,
            self.my_id
        ))
        self.send(data)
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

    def send(self, bytes):
        self.conn.sendall(bytes)

    def recv(self, length):
        bytes = self.conn.recv(length)
        if len(bytes) != length:
            raise IOError("End of stream")
        return bytes


"""    def __init__(self, ip, port, info_hash, my_id):
        self.ip = ip
        self.port = port
        self.info_hash = info_hash
        self.my_id = my_id
        self.choked = True
        self.interested = False
        self.am_choked = True
        self.am_interested = False
        self.timestamp = 0
        self.connection = None
        self.active = False
        self.bitfield = []

    def connect(self):
        try:
            data = "".join((
                chr(19),
                "BitTorrent protocol",
                convert.uint_chr(0, 8),
                self.info_hash,
                self.my_id
            ))
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(2)
            self.connection.connect((self.ip, self.port))
            self.send(data)
            proto_len_b =self.recv(1, True)
            proto_len = ord(proto_len_b)
            if proto_len != 19:
                raise IOError()
            proto = self.recv(proto_len, True)
            if proto != "BitTorrent protocol":
                raise IOError()
            self.recv(8, True)
            info_hash = self.recv(20, True)
            if info_hash != self.info_hash:
                raise IOError()
            self.id = self.recv(20, True)
            self.active = True
            self.read(False)
        except IOError:
            self.close()
        except:
            pass

    def close(self):
        self.connection.close()
        self.connection = None
        self.active = False

    def send(self, bytes):
        self.timestamp = time.time()
        self.connection.sendall(bytes)

    def recv(self, length, tEOS=False):
        bytes = self.connection.recv(length)
        if tEOS and len(bytes) != length:
            raise IOError("End of stream")
        return bytes

    def read(self, raise_error=True):
        length_b = self.recv(4)
        if len(length_b) < 4:
            if raise_error:
                raise ExceptionClass()
            else:
                return
        length = convert.uint_ord(length_b)
        if length == 0:
            return
        command_b = self.recv(1, True)
        command = ord(command_b)
        switch = {
            5: self.read_bitfield
        }
        if command in switch:
            switch[command](length)

    def read_bitfield(self, length):
        raw = self.recv(length - 1)
        if len(raw) == length - 1:
            print "Win", self.id"""
