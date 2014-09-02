import hashlib
import random

import events
import piece
import request


class Downloader(events.EventsModel):
    """This tells which chunks of which pieces you should
    start to download from which peers. It remember all
    pieces and chunks statuses and how many requests
    was sent to each peer. If a chunk was downloaded
    you have to tell it to this with finish() method.


    Events:

        cancel:
            Triggers when a download was canceled.
            It is needed because sometimes client
            have to send a "cancel" message to a peer
            from which it downloads.
            Prototype: on_cancel(node, piece, chunk)
            where node - that peer, piece - what piece
            was downloaded, chunk - what chunk of the piece
            was downloaded.
            To add a handler use: downloader.event_connect("cancel", function).

        finish:
            The torrent was successfully downloaded.
            Prototype: on_finished()
            To add a handler use: downloader.event_connect("finish", function).

        piece:
            A whole piece was downloaded and verified.
            Prototype: on_piece_downloaded(node, piece, data)
            where node - from which peer a piece was downloaded,
            piece - that piece, data - the piece content.
            To add a handler use: downloader.event_connect("piece", function).

    Methods:

        next():
            Tell what chunks need to be downloaded now.
            Return a list of request.Request objects.

        finish(node, piece, chunk, data):
            You have to tell if you have downloaded a chunk.
            You can do that with this method. It stores data,
            checks if the piece is fully downloaded and if it
            is, checks if the piece is valid and writes the piece
            to the disk.

        message():
            Call this in main cycle. It removes timeouts from downloads.

        downloaded():
            Return length of all downloaded data in bytes including bad.

        nodes_count():
            Return a tuple (active peers, all peers).

        progress():
            Return download progress from 0.0 to 1.0 (by downloaded pieces).

        total():
            Return length of all torrent in bytes.

    """

    MAX_ACTIVE_PIECES = 16
    MAX_ACTIVE_CHUNKS = 16
    MAX_REQUESTS = 4
    TIMEOUT = 60

    def __init__(self, nodes, pieces):
        super(Downloader, self).__init__()

        if not isinstance(nodes, list):
            raise TypeError("nodes: expected list")
        if not isinstance(pieces, list):
            raise TypeError("pieces: expected list")

        self._active_pieces = []
        self._all_nodes = nodes
        self._all_pieces = pieces
        self._downloaded_bytes = 0
        self._inactive_pieces = pieces[:]
        self._requests = []

        self.event_init(
            "cancel",
            "finish",
            "piece"
        )

    def next(self):
        """Tell what chunks need to be downloaded now.
        Return a list of request.Request objects.

        """
        if self._is_endgame():
            new_requests = self._next_endgame()
        else:
            new_requests = self._next_normal()
        return new_requests

    def finish(self, n, index, chunk, data):
        """You have to tell if you have downloaded a chunk.
        You can do that with this method. It stores data,
        checks if the piece is fully downloaded and if it
        is, checks if the piece is valid and writes the piece
        to the disk.

        """
        n.active -= 1
        if len(self._all_pieces) <= index:
            return
        p = self._all_pieces[index]
        if len(p.chunks_map) <= chunk:
            return
        p.chunks_map[chunk] = piece.Piece.STATUS_COMPLETE
        p.chunks_buf[chunk] = data
        self._downloaded_bytes += len(data)
        is_full = True
        for buf in p.chunks_buf:
            if not buf:
                is_full = False
                break
        for r in self._requests:
            if (r.node, r.piece, r.chunk) == (n, index, chunk):
                self._requests.remove(r)
                break
        if is_full:
            p_data = "".join(p.chunks_buf)
            p_hash = hashlib.sha1(p_data).digest()
            p.clear()
            if p_hash != p.hash:
                p.alloc()
            else:
                self._active_pieces.remove(p)
                self.event_call("piece", n, p.index, p_data)

    def message(self):
        """Call this in main cycle. It removes timeouts from downloads."""
        for r in self._requests:
            if r.elapsed() >= Downloader.TIMEOUT:
                self._cancel(r)
                break

    def downloaded(self):
        """Return length of all downloaded data in bytes including bad."""
        return self._downloaded_bytes

    def nodes_count(self):
        """Return a tuple (active peers, all peers)."""
        all_len = len(self._all_nodes)
        empty_len = len(self._idle_nodes(only_empty=True))
        return all_len - empty_len, all_len

    def progress(self):
        """Return download progress from 0.0 to 1.0 (by downloaded pieces)."""
        all_len = float(len(self._all_pieces))
        not_downloaded_len = float(len(self._active_pieces) + len(self._inactive_pieces))
        return 1.0 - not_downloaded_len / all_len

    def total(self):
        """Return length of all torrent in bytes."""
        return len(self._all_pieces) * self._all_pieces[0].chunks_count * piece.Piece.CHUNK

    def _cancel(self, r):
        """Remove the request (r) from active requests, rollback
        all statuses to initial state and call on_cancel handlers.

        """
        self._requests.remove(r)
        if r.node in self._all_nodes:
            r.node.active -= 1
        if (
            r.piece < len(self._all_pieces)
            and r.chunk < len(self._all_pieces[r.piece].chunks_map)
        ):
            self._all_pieces[r.piece].chunks_map[r.chunk] = piece.Piece.STATUS_EMPTY
        self.event_call("cancel", r.node, r.piece, r.chunk)

    def _idle_nodes(self, only_empty=False):
        """Return list of all peers which download less than MAX_REQUESTS chunks
        at the moment. If only_empty is True return only peers to which were
        sent no one request.

        """
        nodes = []
        for n in self._all_nodes:
            if n.active < Downloader.MAX_REQUESTS and not only_empty:
                nodes.append(n)
            if n.active == 0 and only_empty:
                nodes.append(n)
        return nodes

    def _is_endgame(self):
        return len(self._inactive_pieces) == 0

    def _next_endgame(self):
        new_requests = []

        for p in self._inactive_pieces:
            p.alloc()
            self._active_pieces.append(p)
        self._inactive_pieces = []

        print "EG!!"

        for p in self._active_pieces:
            for chunk in xrange(len(p.chunks_map)):
                if p.active >= Downloader.MAX_ACTIVE_CHUNKS:
                    break
                if p.chunks_map[chunk] == piece.Piece.STATUS_EMPTY:
                    nodes = []
                    for n in self._all_nodes:
                        if n.get_piece(p.index):
                            nodes.append(n)
                    for n in nodes:
                        p.chunks_map[chunk] = piece.Piece.STATUS_DOWNLOAD
                        n.active += 1
                        if n.active == Downloader.MAX_REQUESTS:
                            nodes.remove(n)
                        r = request.Request(n, p.index, chunk)
                        new_requests.append(r)
                        self._requests.append(r)

        return new_requests

    def _next_normal(self):
        """Compile a list of new requests in normal mode."""
        new_requests = []
        # Get all idle nodes
        idle_nodes = self._idle_nodes()

        # Start to download pieces
        for _ in xrange(Downloader.MAX_ACTIVE_PIECES):
            if (
                len(self._active_pieces) < Downloader.MAX_ACTIVE_PIECES
                and len(self._inactive_pieces)
            ):
                # Check if someone has this piece
                p = self._inactive_pieces[0]
                has_someone = False
                for n in idle_nodes:
                    if n.get_piece(p.index):
                        has_someone = True
                        break
                if not has_someone:
                    continue
                # Start to download a new piece
                p.alloc()
                self._active_pieces.append(p)
                del self._inactive_pieces[0]
            else:
                break

        # Start to download chunks
        for p in self._active_pieces:
            for chunk in xrange(len(p.chunks_map)):
                # Take a free chunk from an active piece if it exists
                # and if the limit of active chunks wasn't reached
                if p.active >= Downloader.MAX_ACTIVE_CHUNKS:
                    break
                if p.chunks_map[chunk] == piece.Piece.STATUS_EMPTY:
                    # Compile list of free peers which have this piece
                    nodes = []
                    for n in idle_nodes:
                        if n.get_piece(p.index):
                            nodes.append(n)
                    if len(nodes):
                        p.chunks_map[chunk] = piece.Piece.STATUS_DOWNLOAD
                        # Take random peer from this list and
                        # remove it from the list if the limit
                        # of requests to one peer was reached
                        n = random.choice(nodes)
                        n.active += 1
                        if n.active == Downloader.MAX_REQUESTS:
                            idle_nodes.remove(n)
                        # Create new request with this peer, piece,
                        # and chunk and add it to requests lists
                        r = request.Request(n, p.index, chunk)
                        new_requests.append(r)
                        self._requests.append(r)

        return new_requests
