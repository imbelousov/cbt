import math

__all__ = ["Chunk", "Piece"]


class Chunk(object):
    """A chunk is the smallest part of torrent.
    All data is downloaded with a lot of chunks.
    Some consecutive chunks constitute a piece.
    Each chunk can store SIZE bytes.

    Attributes:

        buf:
            Stores downloaded data. None if the chunk
            isn't downloaded.

        offset:
            Offset inside the piece.

        download:
            Is chunk active or not.

    """

    SIZE = 16384

    def __init__(self, offset):
        self.buf = None
        self.offset = offset
        self.download = False


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
            Download of the piece is started buf not finished.

        STATUS_COMPLETE:
            The piece is successfully downloaded.

    Attributes:

        chunks:
            List of chunks of the piece.

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

    def __init__(self, hash, length, index):
        self.chunks = []
        self.hash = hash
        self.index = index
        self.length = length
        self.status = Piece.STATUS_EMPTY

    def prepare(self):
        """Prepare all chunks of the piece to download and set
        the status to STATUS_DOWNLOAD.

        """
        chunk_count = int(math.ceil(self.length / Chunk.SIZE))
        for x in xrange(chunk_count):
            chunk = Chunk(x)
            self.chunks.append(chunk)
        self.status = Piece.STATUS_DOWNLOAD

    def complete(self):
        """Clear chunks list and set the status to STATUS_COMPLETE."""
        self.chunks = []
        self.status = Piece.STATUS_COMPLETE
