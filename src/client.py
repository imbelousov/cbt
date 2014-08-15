import hashlib
import os
import socket
import time

import torrent

def singleton(cls):
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return get_instance

VERSION = "-CB0101-"


@singleton
class Client(object):
    def __init__(self):
        torrent.Torrent.set_id(_get_id())
        torrent.Torrent.set_port(_get_port())
        self.torrents = []

    def append(self, filename, path):
        t = torrent.Torrent(filename, path)
        self.torrents.append(t)

    def start(self, index=None):
        if index is None:
            for t in self.torrents:
                t.start()
        else:
            self.torrents[index].start()

    def stop(self, index=None):
        if index is None:
            for t in self.torrents:
                t.stop()
        else:
            self.torrents[index].stop()


def _get_id():
    pid = os.getpid()
    timestamp = time.time()
    unique_str = "".join((
        str(pid),
        str(timestamp)
    ))
    hash = hashlib.sha1(unique_str).digest()
    id = "".join((
        VERSION,
        hash[len(VERSION):]
    ))
    return id

def _get_port(start=6881, end=6890):
    for port in xrange(start, end):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return port
    raise socket.error("Unable to listen any BitTorrent port")
