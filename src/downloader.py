import hashlib

import piece

class Downloader(object):
    MAX_ACTIVE_PIECES = 16
    MAX_ACTIVE_CHUNKS = 16

    def __init__(self, nodes_list, pieces_list):
        self.all_nodes = nodes_list
        self.all_pieces = pieces_list
        self.active_nodes = []
        self.active_pieces = []
        self.inactive_pieces = self.all_pieces[:]

    def next(self):
        result = []
        if (
            len(self.active_pieces) < Downloader.MAX_ACTIVE_PIECES
            and len(self.inactive_pieces)
        ):
            next_piece = self.inactive_pieces[0]
            next_piece.alloc()
            self.active_pieces.append(next_piece)
            del self.inactive_pieces[0]
        for p in self.active_pieces:
            if p.active_chunks >= Downloader.MAX_ACTIVE_CHUNKS:
                continue
            last_chunk = 0
            for n in self.all_nodes:
                if n in self.active_nodes or not n.get_piece(p.index):
                    continue
                for chunk in xrange(last_chunk, len(p.chunks_map)):
                    if p.chunks_map[chunk] != piece.Piece.STATUS_EMPTY:
                        continue
                    self.active_nodes.append(n)
                    p.chunks_map[chunk] = piece.Piece.STATUS_DOWNLOAD
                    result.append((n, p.index, chunk))
                    p.active_chunks += 1
                    last_chunk = chunk
                    break
        return result

    def finish(self, n, index, chunk):
        self.active_nodes.remove(n)
        self.all_pieces[index].chunks_map[chunk] = piece.Piece.STATUS_COMPLETE
        self.all_pieces[index].active_chunks -= 1
        is_full = True
        for status in self.all_pieces[index].chunks_map:
            if status != piece.Piece.STATUS_COMPLETE:
                is_full = False
        if is_full:
            data = "".join(self.all_pieces[index].chunks_buf)
            hash = hashlib.sha1(data).digest()
            if hash != self.all_pieces[index].hash:
                for x in xrange(len(self.all_pieces[index].chunks_map)):
                    self.all_pieces[index].chunks_map[x] = piece.Piece.STATUS_EMPTY
            else:
                print "Downloaded piece %d, Remaining: %d, Active: %d" % (
                    index,
                    len(self.inactive_pieces) + len(self.active_pieces),
                    min(len(self.active_pieces), len(self.active_nodes))
                )
                self.active_pieces.remove(self.all_pieces[index])
