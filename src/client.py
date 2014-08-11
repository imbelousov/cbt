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
        self.gen_id()
        self.gen_port()
        self.torrents = []

    def gen_id(self):
        """Generates unique peer_id"""
        ver = "-CB0100-"
        pid = str(os.getpid())
        timestamp = str(time.time())
        unique_string = "_".join((pid, timestamp))
        unique_hash = hashlib.sha1(unique_string).digest()
        self.id = "".join((ver, unique_hash[len(self.ver):]))

    def gen_port(self):
        """Returns free port"""
        for port in xrange(6881, 6890):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:
                self.port = port
                return
        raise RuntimeError("Unable to listen any BitTorrent port")

    def append_torrent(self, filename, path):
        try:
            with open(filename, "rb") as file:
                contents = file.read()
            t = torrent.Torrent(contents, path, self.id, self.port)
            self.torrents.append(t)
            result = len(self.torrents)
        except:
            result = False
        return result

    def remove_torrent(self, index):
        try:
            self.torrents[index].stop()
            del self.torrents[index]
        except:
            pass

    def get_torrent(self, index):
        return self.torrents[index]