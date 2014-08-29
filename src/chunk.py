__all__ = ["Chunk"]


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

    """

    SIZE = 1 << 14

    def __init__(self, offset):
        self.buf = None
        self.offset = offset
