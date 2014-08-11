#! /usr/bin/python

import hashlib
import os

import bcode
import tracker

__all__ = ["Torrent"]

class Torrent(object):
    def __init__(self, contents, path):
        self.meta = bcode.decode(contents)
        self.tracker = tracker.create(self.meta)
        self.name = self.meta["info"]["name"]
        self.peers = []
        self.active_peers = []
        self.hashes = []
        self.files = []
        self.piece_len = self.meta["info"]["piece length"]
        self.set_path(path)
        self.load_hashes()
        self.load_files()
        self.generate_info_hash()

    def set_path(self, path):
        self.path = os.path.abspath(path)
        if self.path[-1] != os.sep:
            self.path = "".join((self.path, os.sep))

    def load_hashes(self):
        self.hashes = []
        hashes_str = self.meta["info"]["pieces"]
        for i in xrange(0, len(hashes_str), 20):
            self.hashes.append(hashes_str[i:i+20])

    def load_files(self):
        self.files = []
        if "files" in self.meta["info"]:
            for file in self.meta["info"]["files"]:
                self.files.append({
                    "length": file["length"],
                    "name": self.path + os.sep.join(tuple(file["path"])),
                    "path": self.path + os.sep.join(tuple(file["path"][:-1]))
                })
        elif "length" in self.meta["info"]:
            self.files.append({
                "length": self.meta["info"]["length"],
                "name": os.sep.join((self.path, self.name)),
                "path": self.path
            })

    def generate_info_hash(self):
        info_bencode = bcode.encode(self.meta["info"])
        self.info_hash = hashlib.sha1(info_bencode).digest()
