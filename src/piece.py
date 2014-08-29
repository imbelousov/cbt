import math

__all__ = ["Piece"]


class Piece(object):
    """A piece is part of torrent that may be
    verified with SHA1-hash. A piece consists of chunks
    and stores all its chunks until it's downloaded.
    After verification a piece should be written on
    the disk and clear its buffers.

    Each piece has a status:

        STATUS_EMPTY:
            The piece isn't started to download yet.

        STATUS_DOWNLOAD:
            Download of the piece is started but not finished.

        STATUS_COMPLETE:
            The piece is successfully downloaded.

    Attributes:

        chunks:
            List of chunk buffers of the piece.

        hash:
            SHA1-hash of piece data for verification.

        index:
            Position of the piece inside the torrent.

        length:
            Size of downloaded piece.

        status:
            Status of the piece.

    Methods:

        prepare():
            Prepare all chunks of the piece to download and set
            the status to STATUS_DOWNLOAD.

        complete():
            Clear chunks list and set the status to STATUS_COMPLETE.

    """

    STATUS_EMPTY = 0
    STATUS_DOWNLOAD = 1
    STATUS_COMPLETE = 2

    CHUNK = 1 << 14

    def __init__(self, hash, length, index):
        self.chunks_buf = []
        self.chunks_map = []
        self.active_chunks = 0
        self.hash = hash
        self.index = index
        self.length = length

    def alloc(self):
        """Prepare all chunks of the piece to download."""
        chunk_count = int(math.ceil(self.length / Piece.CHUNK))
        for _ in xrange(chunk_count):
            self.chunks_buf.append(None)
            self.chunks_map.append(Piece.STATUS_EMPTY)

    def clear(self):
        """Clear chunks list."""
        self.chunks = []
