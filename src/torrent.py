import hashlib
import socket
import threading

import bcode
import convert
import file
import peer
import tracker


class Torrent(object):

    # Protocol identifier
    PROTOCOL = "BitTorrent protocol"

    # Messages
    MESSAGE_CHOKE = 0
    MESSAGE_UNCHOKE = 1
    MESSAGE_INTERESTED = 2
    MESSAGE_NOTINTERESTED = 3
    MESSAGE_HAVE = 4
    MESSAGE_BITFIELD = 5

    # 20-byte my random identifier
    id = None
    # TCP port for incoming connections.
    port = None

    def __init__(self, filename, path):
        """
        filename - full or relative name of .torrent file
        path - download path

        Torrent.id and Torrent.port are static properties.
        They should be determined before the creating
        a new Torrent instance.

        """
        assert Torrent.id and Torrent.port
        with open(filename, "rb") as f:
            contents = f.read()
        self.meta = bcode.decode(contents)
        self.path = path
        self.tracker = tracker.get(self._tracker_get_urls())
        self.files = self._files_get_list()
        self.hash = self._get_hash()
        self.peers = []

    def start(self):
        """Start the download.

        1. Tell the tracker that I am going to download torrent
        2. Get peers list from the tracker
        3. Try to connect to each peer in list
        4. ...

        """
        self._files_create()
        self.peers = self._tracker_get_peers()
        self._peers_connect()

    def stop(self):
        """Stop the download.

        1. Tell the tracker that I stopped the download
        2. ...

        """
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
        """Return SHA1 hash of bencoded "info" section of the meta."""
        info = bcode.encode(self.meta["info"])
        hash = hashlib.sha1(info).digest()
        return hash

    def _tracker_get_urls(self):
        """Return list of URLs of trackers which specified in the meta."""
        urls = []
        if "announce" in self.meta:
            urls.append(self.meta["announce"])
        if "announce-list" in self.meta:
            for item in self.meta["announce-list"]:
                urls.append(item[0])
        return urls

    def _tracker_get_peers(self):
        """Return list of peers which download or have downloaded
        this torrent too. Send "started" command to tracker.
        Each peer is a peer.Peer object.

        """
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
        """Return list of files which specified in the meta.
        Each file is a file.File object.

        """
        files = []
        # Multifile mode
        if "files" in self.meta["info"]:
            for file_info in self.meta["info"]["files"]:
                f = file.File(
                    intorrent_path=file_info["path"],
                    download_path=self.path,
                    size=file_info["length"]
                )
                files.append(f)
        # Singlefile mode
        if "name" and "length" in self.meta["info"]:
            f = file.File(
                intorrent_path=self.meta["info"]["name"],
                download_path=self.path,
                size=self.meta["info"]["length"]
            )
            files.append(f)
        return files

    def _files_create(self):
        """Allocate memory on disk for each file that specified in meta."""
        for f in self.files:
            f.create()

    def _peers_connect(self):
        conn_threads = []
        for p in self.peers:
            thread = threading.Thread(target=self._peer_connect, args=(p,))
            thread.start()
            conn_threads.append(thread)
        for thread in conn_threads:
            thread.join()

    def _peer_connect(self, p):
        try:
            p.connect()
        except (socket.timeout, socket.error):
            p.close()
            return
        self._peer_send_handshake(p)
        try:
            self._peer_recv_handshake(p)
        except IOError:
            p.close()
            return
        self._peer_recv_messages(p)

    def _peer_send_handshake(self, p):
        """Send the first message to the peer.

        This message should conform to the following format:
            <pstr len><pstr><reserved><info hash><peer id>
        pstr - BitTorrent Protocol identifier.
        pstr len - length of pstr (1 byte)
        reserved - Reserved 8 bytes
        info hash - SHA1 hash of bencoded "info" section in meta
        peer id - 20-byte my random identifier.

        """
        buf = "".join((
            convert.uint_chr(len(Torrent.PROTOCOL), 1),
            Torrent.PROTOCOL,
            convert.uint_chr(0, 8),
            self.hash,
            Torrent.id
        ))
        p.send(buf)

    def _peer_send_message(self, p, buf):
        buf = "".join((
            convert.uint_chr(len(buf)),
            buf
        ))
        p.send(buf)

    def _peer_send_choke(self, p):
        buf = chr(Torrent.MESSAGE_CHOKE)
        self._peer_send_message(p, buf)
        p.c_choked = True

    def _peer_send_unchoke(self, p):
        buf = chr(Torrent.MESSAGE_UNCHOKE)
        self._peer_send_message(p, buf)
        p.c_choked = False

    def _peer_send_interested(self, p):
        buf = chr(Torrent.MESSAGE_INTERESTED)
        self._peer_send_message(p, buf)
        p.c_interested = True

    def _peer_send_notinterested(self, p):
        buf = chr(Torrent.MESSAGE_NOTINTERESTED)
        self._peer_send_message(p, buf)
        p.c_interested = False

    def _peer_recv_handshake(self, p):
        """Receive the first message from the peer.

        This message should conform to the following format:
            <pstr len><pstr><reserved><info hash><peer id>
        pstr - BitTorrent Protocol identifier.
        pstr len - length of pstr (1 byte)
        reserved - Reserved 8 bytes
        info hash - SHA1 hash of bencoded "info" section in meta
        peer id - 20-byte peer identifier.

        Client should close the connection if this message
        is invalid.

        """
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
        p.id = id

    def _peer_recv_messages(self, p):
        while True:
            try:
                self._peer_recv_message(p)
            except socket.error:
                break

    def _peer_recv_choke(self, p, buf):
        if len(buf) != 1:
            raise IOError("Invalid message format")
        p.p_choked = True

    def _peer_recv_unchoke(self, p, buf):
        if len(buf) != 1:
            raise IOError("Invalid message format")
        p.p_choked = False

    def _peer_recv_interested(self, p, buf):
        if len(buf) != 1:
            raise IOError("Invalid message format")
        p.p_interested = True

    def _peer_recv_notinterested(self, p, buf):
        if len(buf) != 1:
            raise IOError("Invalid message format")
        p.p_interested = False

    def _peer_recv_have(self, p, buf):
        if len(buf) != 4:
            raise IOError("Invalid message format")
        piece = convert.uint_ord(buf)
        if piece < len(p.bitfield):
            p.bitfield[piece] = True

    def _peer_recv_bitfield(self, p, buf):
        p.bitfield = []
        for byte in buf:
            byte = ord(byte)
            mask = 0x80
            for _ in range(8):
                bit = bool(byte & mask)
                mask >>= 1
                p.bitfield.append(bit)

    PEER_MESSAGES = {
        MESSAGE_CHOKE: _peer_recv_choke,
        MESSAGE_UNCHOKE: _peer_recv_unchoke,
        MESSAGE_INTERESTED: _peer_recv_interested,
        MESSAGE_NOTINTERESTED: _peer_recv_notinterested,
        MESSAGE_HAVE: _peer_recv_have,
        MESSAGE_BITFIELD: _peer_recv_bitfield
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
            message_handler(self, p, buf)
