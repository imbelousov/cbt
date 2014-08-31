import hashlib
import random
import time

import piece
import request


class Downloader(object):
    """This tells which chunks of which pieces you should
    start to download from which peers. It remember all
    pieces and chunks statuses and how many requests
    was sent to each peer. If a chunk was downloaded
    you have to tell it to this with finish() method.


    Events:

        on_cancel:
            Triggers when a download was canceled.
            It is needed because sometimes client
            have to send a "cancel" message to a peer
            from which it downloads.
            Prototype: on_cancel(node, piece, chunk)
            where node - that peer, piece - what piece
            was downloaded, chunk - what chunk of the piece
            was downloaded.
            To add a handler use: downloader.on_cancel(function).

        on_piece_downloaded:
            A whole piece was downloaded and verified.
            Prototype: on_piece_downloaded(node, piece, data)
            where node - from which peer a piece was downloaded,
            piece - that piece, data - the piece content.
            To add a handler use: downloader.on_piece_downloaded(function).

        on_finished:
            The torrent was successfully downloaded.
            Prototype: on_finished()
            To add a handler use: downloader.on_finished(function).

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

        total():
            Return length of all torrent in bytes.

    Attributes:

        active_pieces:
            List of pieces which are downloading at the moment.

        all_nodes:
            Just a link to peer.nodes.

        all_pieces:
            A link to torrent.pieces.

        inactive_pieces:
            List of pieces which are not started yet.

        requests:
            List of request.Request objects with current downloads.

    """

    MAX_ACTIVE_PIECES = 16
    MAX_ACTIVE_CHUNKS = 16
    MAX_REQUESTS = 4
    TIMEOUT = 60

    def __init__(self, nodes, pieces):
        self.active_pieces = []
        self.all_nodes = nodes
        self.all_pieces = pieces
        self.inactive_pieces = pieces[:]
        self.requests = []

        self.downloaded_bytes = 0
        self.handlers = {
            "on_cancel": [],
            "on_piece_downloaded": [],
            "on_finished": []
        }

    def on_cancel(self, func):
        if func not in self.handlers["on_cancel"]:
            self.handlers["on_cancel"].append(func)

    def on_piece_downloaded(self, func):
        if func not in self.handlers["on_piece_downloaded"]:
            self.handlers["on_piece_downloaded"].append(func)

    def on_finished(self, func):
        if func not in self.handlers["on_finished"]:
            self.handlers["on_finished"].append(func)

    def next(self):
        """Tell what chunks need to be downloaded now.
        Return a list of request.Request objects.

        """
        new_requests = []
        # Get all idle nodes
        idle_nodes = self._idle_nodes()

        # Start to download pieces
        for _ in xrange(Downloader.MAX_ACTIVE_PIECES):
            if (
                len(self.active_pieces) < Downloader.MAX_ACTIVE_PIECES
                and len(self.inactive_pieces)
            ):
                # Check if someone has this piece
                p = self.inactive_pieces[0]
                has_someone = False
                for n in idle_nodes:
                    if n.get_piece(p.index):
                        has_someone = True
                        break
                if not has_someone:
                    continue
                # Start to download a new piece
                p.alloc()
                self.active_pieces.append(p)
                del self.inactive_pieces[0]
            else:
                break

        # Start to download chunks
        for p in self.active_pieces:
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
                        self.requests.append(r)

        return new_requests

    def finish(self, n, index, chunk, data):
        """You have to tell if you have downloaded a chunk.
        You can do that with this method. It stores data,
        checks if the piece is fully downloaded and if it
        is, checks if the piece is valid and writes the piece
        to the disk.

        """
        n.active -= 1
        if len(self.all_pieces) <= index:
            return
        p = self.all_pieces[index]
        if len(p.chunks_map) <= chunk:
            return
        p.chunks_map[chunk] = piece.Piece.STATUS_COMPLETE
        p.chunks_buf[chunk] = data
        self.downloaded_bytes += len(data)
        is_full = True
        for buf in p.chunks_buf:
            if not buf:
                is_full = False
                break
        for r in self.requests:
            if (r.node, r.piece, r.chunk) == (n, index, chunk):
                self.requests.remove(r)
                break
        if is_full:
            p_data = "".join(p.chunks_buf)
            p_hash = hashlib.sha1(p_data).digest()
            p.clear()
            if p_hash != p.hash:
                p.alloc()
            else:
                print (len(self.inactive_pieces) + len(self.active_pieces))
                self.active_pieces.remove(p)
                for func in self.handlers["on_piece_downloaded"]:
                    func(n, p.index, p_data)

    def message(self):
        """Call this in main cycle. It removes timeouts from downloads."""
        cur_time = time.time()
        for r in self.requests:
            if cur_time - r.started_at >= Downloader.TIMEOUT:
                self._cancel(r)
                break

    def downloaded(self):
        """Return length of all downloaded data in bytes including bad."""
        return self.downloaded_bytes

    def total(self):
        """Return length of all torrent in bytes."""
        return len(self.all_pieces) * self.all_pieces[0].chunks_count * piece.Piece.CHUNK

    def _idle_nodes(self):
        """Return list of all peers which download less than MAX_REQUESTS chunks
        at the moment.

        """
        nodes = []
        for n in self.all_nodes:
            if n.active < Downloader.MAX_REQUESTS:
                nodes.append(n)
        return nodes

    def _cancel(self, r):
        """Remove the request (r) from active requests, rollback
        all statuses to initial state and call on_cancel handlers.

        """
        self.requests.remove(r)
        if r.node in self.all_nodes:
            r.node.active -= 1
        if (
            r.piece < len(self.all_pieces)
            and r.chunk < len(self.all_pieces[r.piece].chunks_map)
        ):
            self.all_pieces[r.piece].chunks_map[r.chunk] = piece.Piece.STATUS_EMPTY
        for func in self.handlers["on_cancel"]:
            func(r.node, r.piece, r.chunk)
