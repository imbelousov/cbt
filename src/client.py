#! /usr/bin/python

import os
import time
import hashlib
import socket

import torrent

__all__ = ["Client"]

class Client(object):
    def __init__(self):
        self.ver = "-CB0100-"
        self.torrents = []
        self._gen_id()
        self._gen_port()

    def append(self, filename, path):
        with open(filename, "rb") as file:
            contents = file.read()
        t = torrent.Torrent(contents, path, self.id, self.port)
        self.torrents.append(t)

    def remove(self, index):
        if not self.get(index):
            return
        self.torrents[index].stop()
        del self.torrents[index]

    def get(self, index):
        if index >= 0 and index < self.length():
            return self.torrents[index]
        return None

    def length(self):
        return len(self.torrents)

    def _gen_id(self):
        """Generates unique peer_id"""
        ver = "-CB0100-"
        pid = str(os.getpid())
        timestamp = str(time.time())
        unique_string = "_".join((pid, timestamp))
        unique_hash = hashlib.sha1(unique_string).digest()
        self.id = "".join((ver, unique_hash[len(self.ver):]))

    def _gen_port(self):
        """Returns free port"""
        for port in xrange(6881, 6890):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:
                self.port = port
                return
        raise RuntimeError("Unable to listen any BitTorrent port")
