import hashlib

import piece
import writer


class Downloader(object):
    """This tells which chunks of which pieces you should
    start to download from which peers. It remember all
    pieces and chunks statuses and how many requests
    was sent to each peer. If a chunk was downloaded
    you have to tell it to this with finish() method.

    Methods:

        next():
            Tell what chunks need to be downloaded now.
            Return a list of tuples: (node, piece, chunk)
            where node - from what peer you can download,
            piece - index of a downloadable piece and
            chunk - index of an empty chunk inside the piece.

        finish(node, piece, chunk, data):
            You have to tell if you have downloaded a chunk.
            You can do that with this method. It stores data,
            checks if the piece is fully downloaded and if it
            is, checks if the piece is valid and writes the piece
            to the disk.

        downloaded():
            Return length of all downloaded data in bytes including bad.

        total():
            Return length of all torrent in bytes.

    Attributes:

        writer:
            A writer.Writer object for this torrent.

    """

    MAX_ACTIVE_PIECES = 16
    MAX_ACTIVE_CHUNKS = 16
    MAX_REQUESTS = 4

    def __init__(self, nodes, pieces):
        self.all_nodes = nodes
        self.all_pieces = pieces
        # Downloading pieces
        self.active_pieces = []
        # Pieces which are not started yet
        self.inactive_pieces = pieces[:]
        self.downloaded_bytes = 0
        self.writer = writer.Writer()

    def next(self):
        """Tell what chunks need to be downloaded now.
        Return a list of tuples: (node, piece, chunk)
        where node - from what peer you can download,
        piece - index of a downloadable piece and
        chunk - index of an empty chunk inside the piece.

        """
        nodes_pieces_chunks = []
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
                if p.active >= Downloader.MAX_ACTIVE_CHUNKS:
                    break
                if p.chunks_map[chunk] == piece.Piece.STATUS_EMPTY:
                    for n in idle_nodes:
                        if n.get_piece(p.index):
                            n.active += 1
                            if n.active == Downloader.MAX_REQUESTS:
                                idle_nodes.remove(n)
                            p.chunks_map[chunk] = piece.Piece.STATUS_DOWNLOAD
                            nodes_pieces_chunks.append((n, p.index, chunk))
                            break

        return nodes_pieces_chunks

    def finish(self, n, index, chunk, data):
        """You have to tell if you have downloaded a chunk.
        You can do that with this method. It stores data,
        checks if the piece is fully downloaded and if it
        is, checks if the piece is valid and writes the piece
        to the disk.

        """
        n.active -= 1
        p = self.all_pieces[index]
        p.chunks_map[chunk] = piece.Piece.STATUS_COMPLETE
        p.chunks_buf[chunk] = data
        self.downloaded_bytes += len(data)
        is_full = True
        for buf in p.chunks_buf:
            if not buf:
                is_full = False
                break
        if is_full:
            p_data = "".join(p.chunks_buf)
            p_hash = hashlib.sha1(p_data).digest()
            p.clear()
            if p_hash != p.hash:
                p.alloc()
            else:
                self.active_pieces.remove(p)
                self.writer.write(p.index * p.length, p_data)

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
