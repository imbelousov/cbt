import hashlib
import os
import socket
import time

import bcode
import convert
import file
import piece
import peer
import tracker

VERSION = "-CB0101-"


def gen_id():
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


def gen_port(start=6881, end=6890):
    for port in xrange(start, end):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:
            return port
    raise socket.error("Unable to listen any BitTorrent port")


class Torrent(object):
    id = None
    port = None

    def __init__(self, torrent_path, download_path):
        if not Torrent.id:
            Torrent.id = gen_id()
        if not Torrent.port:
            Torrent.port = gen_port()

        self.torrent_path = torrent_path
        self.download_path = download_path
        self.files = []
        self.meta = {}
        self.hash = ""
        self.tracker = None
        self.peer = peer.Peer()
        self.pieces = []

        self.peer.on_recv(self.on_recv)
        self.peer.on_recv_handshake(self.on_recv_handshake)

        # Load meta data from .torrent
        with open(self.torrent_path, "rb") as f:
            self.meta = bcode.decode(f.read())
        self.hash = hashlib.sha1(bcode.encode(self.meta["info"])).digest()

        # Load files info
        # Multifile mode
        if "files" in self.meta["info"]:
            for file_info in self.meta["info"]["files"]:
                f = file.File(
                    intorrent_path=file_info["path"],
                    download_path=self.download_path,
                    size=file_info["length"]
                )
                self.files.append(f)
        # Singlefile mode
        if "name" and "length" in self.meta["info"]:
            f = file.File(
                intorrent_path=self.meta["info"]["name"],
                download_path=self.download_path,
                size=self.meta["info"]["length"]
            )
            self.files.append(f)

        # Load pieces info
        piece_count = len(self.meta["info"]["pieces"]) / 20
        piece_length = self.meta["info"]["piece length"]
        for x in xrange(piece_count):
            hash = self.meta["info"]["pieces"][x*20:x*20+20]
            p = piece.Piece(hash, piece_length)
            self.pieces.append(p)

        # Load trackers list and select available
        trackers = []
        if "announce" in self.meta:
            trackers.append(self.meta["announce"])
        if "announce-list" in self.meta:
            for item in self.meta["announce-list"]:
                trackers.append(item[0])
        self.tracker = tracker.get(trackers)

    def start(self):
        for f in self.files:
            f.create()
        response = self.tracker.request(
            hash=self.hash,
            id=Torrent.id,
            port=Torrent.port,
            uploaded=0,
            downloaded=0,
            left=0,
            event="started"
        )
        if type(response["peers"]) is str:
            for x in xrange(0, len(response["peers"]), 6):
                ip = ".".join([str(ord(byte)) for byte in response["peers"][x:x+4]])
                port = convert.uint_ord(response["peers"][x+4:x+6])
                self.peer.append_node(ip, port)
        self.peer.connect_all()
        buf = "".join((
            chr(len(peer.Peer.PROTOCOL)),
            peer.Peer.PROTOCOL,
            convert.uint_chr(0, 8),
            self.hash,
            Torrent.id
        ))
        for n in self.peer.nodes:
            n.send(buf)

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

    def send_unchoke(self, n):
        buf = "".join((
            convert.uint_chr(1),
            chr(1)
        ))
        n.send(buf)

    def send_interested(self, n):
        buf = "".join((
            convert.uint_chr(1),
            chr(2)
        ))
        n.send(buf)

    def handle_have(self, n, piece):
        bitfield_len = len(n.bitfield)
        if piece >= bitfield_len:
            for _ in xrange(bitfield_len - piece + 1):
                n.bitfield.append(False)
        n.bitfield[piece] = True

    def handle_bitfield(self, n, buf):
        n.bitfield = []
        for byte in buf:
            mask = 0x80
            byte = ord(byte)
            for x in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                n.bitfield.append(bit)
        print "BITFIELD LEN", len(n.bitfield)

    MESSAGE_HAVE = 4
    MESSAGE_BITFIELD = 5

    def on_recv(self, n, buf):
        if not n.handshaked:
            n.close()
            return
        if len(buf) == 4 and convert.uint_ord(buf) == 0:
            # Keep-alive message
            n.send(convert.uint_chr(0))
            print "KA", n.ip
            return
        m_type = ord(buf[4])
        if m_type == Torrent.MESSAGE_HAVE:
            self.handle_have(n, convert.uint_ord(buf[5:9]))
        elif m_type == Torrent.MESSAGE_BITFIELD:
            self.handle_bitfield(n, buf[5:])
        print "ME", m_type, n.ip

    def on_recv_handshake(self, n, buf):
        pstr_len = ord(buf[0])
        pstr = buf[1:pstr_len+1]
        if pstr != peer.Peer.PROTOCOL:
            n.close()
            return
        hash = buf[9+pstr_len:29+pstr_len]
        if hash != self.hash:
            n.close()
            return
        n.id = buf[29+pstr_len:49+pstr_len]
        n.handshaked = True
        print "HS", n.ip

    def message(self):
        self.peer.message()
