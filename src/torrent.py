#! /usr/bin/python

import hashlib
import threading

import bcode
import tracker
import peer
import file
import convert

__all__ = ["Torrent"]

class Torrent(object):
    def __init__(self, contents, path, my_id, my_port):
        self.meta = bcode.decode(contents)
        self.path = path
        self.my_id = my_id
        self.my_port = my_port
        self.files = []
        self._load_files()
        self.peers = []
        self.tracker = tracker.get(self.meta)
        self._load_info_hash()

    def start(self):
        for f in self.files:
            f.create()
        self._load_peers()
        p_threads = []
        for p in self.peers:
            p_thread = threading.Thread(target = p.connect, args = ())
            p_thread.start()
            p_threads.append(p_thread)
        for p_thread in p_threads:
            p_thread.join()
        for p in self.peers:
            if p.is_available(0):
                p.set_choked(False)
                p.set_interested(True)
                print p.p_ip
                print "c_choked:", p.c_choked
                print "p_choked:", p.p_choked
                print "c_interested:", p.c_interested
                print "p_interested:", p.p_interested
                break

    def stop(self):
        self.tracker.request(
            info_hash = self.info_hash,
            peer_id = self.my_id,
            port = self.my_port,
            uploaded = 0,
            downloaded = self.get_downloaded(),
            left = self.get_left(),
            event = "stopped"
        )

    def get_downloaded(self):
        return 0

    def get_left(self):
        return sum([f.length for f in self.files])

    def _load_files(self):
        if "files" in self.meta["info"]:
            # Multifile mode
            for file_info in self.meta["info"]["files"]:
                f = file.File(file_info["path"], self.path, file_info["length"])
                self.files.append(f)
        elif "name" and "length" in self.meta["info"]:
            # Singlefile mode
            f = file.File(self.meta["info"]["name"], self.path, self.meta["info"]["length"])
            self.files.append(f)

    def _load_peers(self):
        t_info = self.tracker.request(
            info_hash = self.info_hash,
            peer_id = self.my_id,
            port = self.my_port,
            uploaded = 0,
            downloaded = self.get_downloaded(),
            left = self.get_left(),
            event = "started"
        )
        if type(t_info["peers"]) is str:
            p_bytes = t_info["peers"]
            for x in xrange(0, len(p_bytes), 6):
                p_ip = ".".join([str(ord(byte)) for byte in p_bytes[x+0:x+4]])
                p_port = convert.uint_ord(p_bytes[x+4:x+6])
                p_info_hash = self.info_hash
                p_my_id = self.my_id
                self.peers.append(peer.Peer(p_ip, p_port, p_info_hash, p_my_id))

    def _load_info_hash(self):
        info_bencode = bcode.encode(self.meta["info"])
        self.info_hash = hashlib.sha1(info_bencode).digest()
