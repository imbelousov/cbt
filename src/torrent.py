import hashlib

import bcode
import convert
import file
import peer
import tracker

class Torrent(object):
    id = None
    port = None

    def __init__(self, filename, path):
        assert Torrent.id is not None
        assert Torrent.port is not None
        with open(filename, "rb") as f:
            contents = f.read()
        self.meta = bcode.decode(contents)
        self.path = path
        self.tracker = tracker.get(self._tracker_get_urls())
        self.files = self._files_get_list()
        self.hash = self._get_hash()
        self.peers = []

    @staticmethod
    def set_id(id_):
        Torrent.id = id_

    @staticmethod
    def set_port(port):
        Torrent.port = port

    def start(self):
        self._files_create()
        self.peers = self._tracker_get_peers()
        for p in self.peers:
            print p.ip, p.port

    def stop(self):
        self.tracker.request(
            hash=self.hash,
            id=Torrent.id,
            port=Torrent.port,
            uploaded=0,
            downloaded=0,
            left=0,
            event="stopped"
        )

    def _get_hash(self):
        info = bcode.encode(self.meta["info"])
        hash_ = hashlib.sha1(info).digest()
        return hash_

    def _tracker_get_urls(self):
        urls = []
        if "announce" in self.meta:
            urls.append(self.meta["announce"])
        if "announce-list" in self.meta:
            for item in self.meta["announce-list"]:
                urls.append(item[0])
        return urls

    def _tracker_get_peers(self):
        peers = []
        info = self.tracker.request(
            hash=self.hash,
            id=Torrent.id,
            port=Torrent.port,
            uploaded=0,
            downloaded=0,
            left=0,
            event="started"
        )
        if type(info["peers"]) is str:
            peers_bytes = info["peers"]
            for x in xrange(0, len(peers_bytes), 6):
                ip = ".".join([str(ord(byte)) for byte in peers_bytes[x+0:x+4]])
                port = convert.uint_ord(peers_bytes[x+4:x+6])
                p = peer.Peer(ip, port)
                peers.append(p)
        return peers

    def _files_get_list(self):
        files = []
        if "files" in self.meta["info"]:
            for file_info in self.meta["info"]["files"]:
                f = file.File(
                    intorrent_path=file_info["path"],
                    download_path=self.path,
                    size=file_info["length"]
                )
                files.append(f)
        if "name" and "length" in self.meta["info"]:
            f = file.File(
                intorrent_path=self.meta["info"]["name"],
                download_path=self.path,
                size=self.meta["info"]["length"]
            )
            files.append(f)
        return files

    def _files_create(self):
        for f in self.files:
            f.create()
