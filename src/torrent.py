import hashlib
import math
import os
import random
import socket
import time

import bcode
import convert
import file
import piece
import peer
import tracker

VERSION = "-CB0101-"

collected = []


def collect(cls):
    class Collector(cls):
        def __init__(self, *args, **kwargs):
            super(Collector, self).__init__(*args, **kwargs)
            collected.append(self)
    return Collector


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


def main_loop():
    try:
        while True:
            for obj in collected:
                obj.message()
    except KeyboardInterrupt:
        pass


class Download(object):
    STATUS_STARTED = 0
    STATUS_UNCHOKING = 1
    STATUS_UNCHOKED = 2
    STATUS_DOWNLOADING = 3

    def __init__(self):
        self.piece = None
        self.chunk = None
        self.node = None
        self.status = Download.STATUS_STARTED
        self.started_at = time.time()


class Info(object):
    def __init__(self):
        self.total_downloaded = 0
        self.total_downloaded_pieces = 0
        self.session_downloaded = 0
        self.session_started_at = 0

    def downloaded(self, size):
        self.total_downloaded += size
        self.session_downloaded += size

    def finished_piece(self):
        self.total_downloaded_pieces += 1

    def session_start(self):
        self.session_started_at = time.time()
        self.session_downloaded = 0

    def session_time(self):
        return time.time() - self.session_started_at

    def session_speed(self):
        t = self.session_time()
        if t == 0:
            return 0
        return int(self.session_downloaded / t)


@collect
class Torrent(object):
    MESSAGE_CHOKE = 0
    MESSAGE_UNCHOKE = 1
    MESSAGE_INTERESTED = 2
    MESSAGE_NOTINTERESTED = 3
    MESSAGE_HAVE = 4
    MESSAGE_BITFIELD = 5
    MESSAGE_REQUEST = 6
    MESSAGE_PIECE = 7
    MESSAGE_CANCEL = 8

    MAX_ACTIVE_PIECES = 8
    MAX_ACTIVE_CHUNKS = 16

    SHOW_FREQUENCY = 5

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
        self.downloads = []
        self.info = Info()

        self.peer.on_recv(self.handle_message)
        self.peer.on_recv_handshake(self.handle_handshake)

        # Load meta data from .torrent
        with open(self.torrent_path, "rb") as f:
            self.meta = bcode.decode(f.read())
        self.hash = hashlib.sha1(bcode.encode(self.meta["info"])).digest()

        # Load files info
        # Multifile mode
        offset = 0
        if "files" in self.meta["info"]:
            for file_info in self.meta["info"]["files"]:
                f = file.File(
                    intorrent_path=file_info["path"],
                    download_path=self.download_path,
                    size=file_info["length"],
                    offset=offset
                )
                offset += file_info["length"]
                self.files.append(f)
        # Singlefile mode
        if "name" and "length" in self.meta["info"]:
            f = file.File(
                intorrent_path=self.meta["info"]["name"],
                download_path=self.download_path,
                size=self.meta["info"]["length"],
                offset=0
            )
            self.files.append(f)

        # Load pieces info
        piece_count = len(self.meta["info"]["pieces"]) / 20
        piece_length = self.meta["info"]["piece length"]
        for x in xrange(piece_count):
            hash = self.meta["info"]["pieces"][x*20:x*20+20]
            p = piece.Piece(hash, piece_length, len(self.pieces))
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
                ip = ".".join((str(ord(byte)) for byte in response["peers"][x:x+4]))
                port = convert.uint_ord(response["peers"][x+4:x+6])
                self.peer.append_node(ip, port)
        self.peer.connect_all()
        for n in self.peer.nodes:
            self.send_handshake(n)
            self.send_bitfield(n)

    def regular_request(self):
        result = self.tracker.request(
            hash=self.hash,
            id=Torrent.id,
            port=Torrent.port,
            uploaded=0,
            downloaded=self.downloaded,
            left=0,
            event=""
        )

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

    def message(self):
        self.peer.message()
        self.download_piece()
        self.show_info()

    def download_piece(self):
        # Try to start to download a new piece
        active_pieces = sum((1 for p in self.pieces if p.status == piece.Piece.STATUS_DOWNLOAD))
        if active_pieces < Torrent.MAX_ACTIVE_PIECES:
            for p in self.pieces:
                if p.status != piece.Piece.STATUS_EMPTY:
                    continue
                nodes = self.get_nodes(p.index)
                if not len(nodes):
                    continue
                p.prepare()
                break

        # Try to start to download a new chunk
        for p in self.pieces:
            if p.status != piece.Piece.STATUS_DOWNLOAD:
                continue
            active_chunks = sum((1 for d in self.downloads if d.piece == p))
            if active_chunks == Torrent.MAX_ACTIVE_CHUNKS:
                continue
            chunks = [c for c in p.chunks if not c.download and not c.buf]
            nodes = self.get_nodes(p.index)
            if not len(chunks) or not len(nodes):
                continue
            d = Download()
            d.node = random.choice(nodes)
            d.chunk = chunks[0]
            d.chunk.download = True
            d.piece = p
            if not d.node.p_choke:
                d.status = Download.STATUS_UNCHOKED
            self.downloads.append(d)
            break

        # Manage chunk downloads
        cur_time = time.time()
        for d in self.downloads:
            if d.status == Download.STATUS_STARTED:
                self.send_unchoke(d.node)
                d.node.sleep(5)
                self.send_interested(d.node)
                d.status = Download.STATUS_UNCHOKING
            if d.status == Download.STATUS_UNCHOKED:
                self.send_request(d.node, d.piece.index, piece.Chunk.SIZE * d.chunk.offset, piece.Chunk.SIZE)
                d.status = Download.STATUS_DOWNLOADING
            if cur_time - d.started_at > 30:
                if d.status == Download.STATUS_DOWNLOADING:
                    self.send_cancel(d.node, d.piece.index, piece.Chunk.SIZE * d.chunk.offset, piece.Chunk.SIZE)
                d.chunk.download = False
                self.downloads.remove(d)
                break
            if d.node not in self.peer.nodes:
                d.chunk.download = False
                self.downloads.remove(d)
                break

        # Try to compile a piece from chunks
        # TODO: drag this to handle_piece to reduce the load
        for p in self.pieces:
            if p.status != piece.Piece.STATUS_DOWNLOAD:
                continue
            is_full = True
            for c in p.chunks:
                if not c.buf:
                    is_full = False
                    break
            if is_full:
                data = "".join((c.buf for c in p.chunks))
                if p.hash != hashlib.sha1(data).digest():
                    p.status = piece.Piece.STATUS_EMPTY
                    p.chunks = []
                    break
                self.write(p.index * len(data), data)
                p.complete()
                self.info.downloaded(len(data))
                self.info.finished_piece()

    def get_nodes(self, index):
        nodes = []
        for n in self.peer.nodes:
            if (
                len(n.bitfield) > index
                and n.bitfield[index]
                and n not in (d.node for d in self.downloads)
            ):
                nodes.append(n)
        return nodes

    def show_info(self):
        if self.info.session_time() < Torrent.SHOW_FREQUENCY:
            return
        speed = self.info.session_speed()
        downloaded = self.info.total_downloaded
        for p in self.pieces:
            if p.status != piece.Piece.STATUS_DOWNLOAD:
                continue
            for c in p.chunks:
                if not c.buf:
                    continue
                downloaded += len(c.buf)
        self.info.session_start()
        length = math.ceil(self.meta["info"]["piece length"] * len(self.meta["info"]["pieces"]) / 20)
        progress = "%.2f%%" % (downloaded / length * 100)
        print "[%s] [Speed: %.1f KB/s] [Chunks: %d] [Peers: %d] [Downloaded: %.0f KB]" % (
            progress,
            speed / 1024.0,
            len(self.downloads),
            len(self.peer.nodes),
            downloaded / 1024.0
        )

    def handle_message(self, n, buf):
        if not n.handshaked:
            # Invalid peer
            n.close()
            return
        if len(buf) == 4 and convert.uint_ord(buf) == 0:
            # Keep-alive message
            n.send(convert.uint_chr(0))
            return
        # Other messages
        m_type = ord(buf[4])
        if m_type == Torrent.MESSAGE_CHOKE:
            self.handle_choke(n)
        elif m_type == Torrent.MESSAGE_UNCHOKE:
            self.handle_unchoke(n)
        elif m_type == Torrent.MESSAGE_INTERESTED:
            self.handle_interested(n)
        elif m_type == Torrent.MESSAGE_NOTINTERESTED:
            self.handle_notinterested(n)
        elif m_type == Torrent.MESSAGE_HAVE:
            self.handle_have(n, buf[5:])
        elif m_type == Torrent.MESSAGE_BITFIELD:
            self.handle_bitfield(n, buf[5:])
        elif m_type == Torrent.MESSAGE_PIECE:
            self.handle_piece(n, buf[5:])
        else:
            pass

    def handle_handshake(self, n, buf):
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

    def handle_choke(self, n):
        n.p_choke = True

    def handle_unchoke(self, n):
        n.p_choke = False
        for d in self.downloads:
            if d.node == n:
                d.status = Download.STATUS_UNCHOKED

    def handle_interested(self, n):
        n.p_interested = True

    def handle_notinterested(self, n):
        n.p_interested = False

    def handle_have(self, n, buf):
        index = convert.uint_ord(buf[0:4])
        bitfield_len = len(n.bitfield)
        if index >= bitfield_len:
            for _ in xrange(bitfield_len - index + 1):
                n.bitfield.append(False)
        n.bitfield[index] = True

    def handle_bitfield(self, n, buf):
        n.bitfield = []
        for byte in buf:
            mask = 0x80
            byte = ord(byte)
            for x in xrange(8):
                bit = bool(byte & mask)
                mask >>= 1
                n.bitfield.append(bit)

    def handle_piece(self, n, buf):
        index = convert.uint_ord(buf[0:4])
        begin = convert.uint_ord(buf[4:8])
        data = buf[8:]
        for d in self.downloads:
            if d.piece.index != index or d.chunk.offset * piece.Chunk.SIZE != begin:
                continue
            d.chunk.buf = data
            d.chunk.download = False
            self.downloads.remove(d)
            break

    def send_handshake(self, n):
        buf = "".join((
            chr(len(peer.Peer.PROTOCOL)),
            peer.Peer.PROTOCOL,
            convert.uint_chr(0, 8),
            self.hash,
            Torrent.id
        ))
        n.send(buf)

    def send_message(self, n, message):
        buf = "".join((
            convert.uint_chr(len(message)),
            message
        ))
        n.send(buf)

    def send_choke(self, n):
        self.send_message(n, chr(Torrent.MESSAGE_CHOKE))
        n.c_choke = True

    def send_unchoke(self, n):
        self.send_message(n, chr(Torrent.MESSAGE_UNCHOKE))
        n.c_choke = False

    def send_interested(self, n):
        self.send_message(n, chr(Torrent.MESSAGE_INTERESTED))
        n.c_interested = True

    def send_notinterested(self, n):
        self.send_message(n, chr(Torrent.MESSAGE_NOTINTERESTED))
        n.c_interested = False

    def send_have(self, n, index):
        buf = "".join((
            chr(Torrent.MESSAGE_HAVE),
            convert.uint_chr(index)
        ))
        self.send_message(n, buf)

    def send_bitfield(self, n):
        count = int(math.ceil(len(self.pieces) / 8))
        buf = [chr(Torrent.MESSAGE_BITFIELD)]
        for _ in xrange(count):
            buf.append(chr(0))
        self.send_message(n, "".join(buf))

    def send_request(self, n, index, begin, length):
        buf = "".join((
            chr(Torrent.MESSAGE_REQUEST),
            convert.uint_chr(index),
            convert.uint_chr(begin),
            convert.uint_chr(length)
        ))
        self.send_message(n, buf)

    def send_cancel(self, n, index, begin, length):
        buf = "".join((
            chr(Torrent.MESSAGE_CANCEL),
            convert.uint_chr(index),
            convert.uint_chr(begin),
            convert.uint_chr(length)
        ))
        self.send_message(n, buf)

    def write(self, offset, data):
        for f in self.files:
            if f.offset <= offset < f.offset + f.size:
                part_len = False
                offset -= f.offset
                if offset + len(data) > f.size:
                    part_len = f.size - offset
                if part_len:
                    self.write(offset + part_len, data[part_len:])
                    data = data[:part_len]
                with open(f.name, "r+b") as fd:
                    fd.seek(offset)
                    fd.write(data)
                break
