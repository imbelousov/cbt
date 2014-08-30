import hashlib

import piece


class Downloader(object):
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

    def next(self):
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
        n.active -= 1
        p = self.all_pieces[index]
        p.chunks_map[chunk] = piece.Piece.STATUS_COMPLETE
        p.chunks_buf[chunk] = data
        self.downloaded_bytes += len(data)
        print "%d / %d" % (
            self.downloaded(),
            self.total()
        )
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

    def downloaded(self):
        return self.downloaded_bytes

    def total(self):
        return len(self.all_pieces) * self.all_pieces[0].chunks_count * piece.Piece.CHUNK

    def _idle_nodes(self):
        nodes = []
        for n in self.all_nodes:
            if n.active < Downloader.MAX_REQUESTS:
                nodes.append(n)
        return nodes
