__all__ = ["Chunk"]


class Chunk(object):
    """A chunk is the smallest part of torrent.
    All data is downloaded with a lot of chunks.
    Some consecutive chunks constitute a piece.
    Each chunk can store SIZE bytes.

    Each chunk has a status:

        STATUS_EMPTY:
            The chunk isn't started to download yet.

        STATUS_DOWNLOAD:
            Download of the chunk is started but not finished.

        STATUS_COMPLETE:
            The chunk is successfully downloaded.

    Attributes:

        buf:
            Stores downloaded data. None if the chunk
            isn't downloaded.

        index:
            Index of the parent piece.

        offset:
            Offset inside the piece.

        status:
            Status of the chunk.
    """

    SIZE = 1 << 14

    STATUS_EMPTY = 0
    STATUS_DOWNLOAD = 1
    STATUS_COMPLETE = 2

    def __init__(self, index, offset):
        self.buf = None
        self.index = index
        self.offset = offset
        self.status = Chunk.STATUS_EMPTY
