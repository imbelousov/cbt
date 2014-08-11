#! /usr/bin/python

import time
import socket

import net

__all__ = ["Peer"]

class Peer(object):
    def __init__(self, ip, port, info_hash, my_id):
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

    def connect(self):
        try:
            data = "".join((
                chr(19),
                "BitTorrent protocol",
                net.uint_chr(0, 8),
                self.info_hash,
                self.my_id
            ))
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(2)
            self.connection.connect((self.ip, self.port))
            self.send(data)
            response = self.connection.recv(128)
            if len(response) < 49:
                raise RuntimeError()
            proto_len = ord(response[0])
            proto = response[1:proto_len+1]
            if proto != "BitTorrent protocol":
                raise RuntimeError()
            info_hash = response[proto_len+9:proto_len+29]
            if info_hash != self.info_hash:
                raise RuntimeError()
            self.id = response[proto_len+29:proto_len+49]
            self.active = True
        except:
            self.close()
        self.choke()

    def close(self):
        self.connection.close()
        self.connection = None
        self.active = False

    def choke(self):
        if not self.active:
            return
        data = "".join((
            net.uint_chr(1),
            "0"
        ))
        self.send(data)
        response = self.connection.recv(1024)
        self.read(response)

    def send(self, bytes):
        self.timestamp = time.time()
        self.connection.sendall(bytes)

    def read(self, bytes):
        if len(bytes) < 4:
            return
        s = ""
        for b in bytes[0:10]:
            s += str(net.uint_ord(b)) + ", "
        print s
