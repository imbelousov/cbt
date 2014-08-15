import hashlib
import socket

import bcode
import convert
import file
import peer
import tracker

class Torrent(object):
    PROTOCOL = "BitTorrent protocol"

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
    def set_id(id):
        Torrent.id = id

    @staticmethod
    def set_port(port):
        Torrent.port = port

    def start(self):
        self._files_create()
        self.peers = self._tracker_get_peers()
        self._peers_connect()

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
        hash = hashlib.sha1(info).digest()
        return hash

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
            peers_b = info["peers"]
            for x in xrange(0, len(peers_b), 6):
                ip = ".".join([str(ord(byte)) for byte in peers_b[x+0:x+4]])
                port = convert.uint_ord(peers_b[x+4:x+6])
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

    def _peers_connect(self):
        for p in self.peers:
            p.connect()
            self._peer_send_handshake(p)
            try:
                self._peer_recv_handshake(p)
            except IOError:
                p.close()
                continue
            self._peer_recv(p)

    def _peer_send_handshake(self, p):
        buf = "".join((
            convert.uint_chr(len(Torrent.PROTOCOL), 1),
            Torrent.PROTOCOL,
            convert.uint_chr(0, 8),
            self.hash,
            Torrent.id
        ))
        p.send(buf)

    def _peer_recv_handshake(self, p):
        # Protocol identifier
        pstr_len_b = p.recv(1)
        pstr_len = convert.uint_ord(pstr_len_b)
        if pstr_len != len(Torrent.PROTOCOL):
            raise IOError("Unknown peer protocol")
        pstr = p.recv(pstr_len)
        if pstr != Torrent.PROTOCOL:
            raise IOError("Unknown peer protocol")
        # Reserved bytes
        p.recv(8)
        # Check if peer really has this torrent
        hash = p.recv(20)
        if hash != self.hash:
            raise IOError("Torrents are not the same")
        # Get peer id and save
        id = p.recv(20)
        p.set_id(id)

    def _peer_recv(self, p):
        while True:
            try:
                self._peer_recv_message(p)
            except socket.error:
                break

    def _peer_recv_choke(self, buf):
        pass

    def _peer_recv_unchoke(self, buf):
        pass

    def _peer_recv_interested(self, buf):
        pass

    def _peer_recv_notinterested(self, buf):
        pass

    def _peer_recv_have(self, buf):
        pass

    def _peer_recv_bitfield(self, buf):
        pass

    PEER_MESSAGES = {
        0: _peer_recv_choke,
        1: _peer_recv_unchoke,
        2: _peer_recv_interested,
        3: _peer_recv_notinterested,
        4: _peer_recv_have,
        5: _peer_recv_bitfield
    }

    def _peer_recv_message(self, p):
        message_len_b = p.recv(4)
        message_len = convert.uint_ord(message_len_b)
        if message_len == 0:
            # Keep-alive message
            return
        message_type_b = p.recv(1)
        message_type = convert.uint_ord(message_type_b)
        buf = p.recv(message_len - 1)
        if message_type in Torrent.PEER_MESSAGES:
            message_handler = Torrent.PEER_MESSAGES[message_type]
            message_handler(self, buf)
