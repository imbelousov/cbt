import math

STATUS_EMPTY = 0
STATUS_DOWNLOAD = 1
STATUS_COMPLETE = 2


class Chunk(object):
    def __init__(self, offset):
        self.buf = None
        self.offset = offset
        self.status = STATUS_EMPTY

    def prepare(self):
        pass

    def complete(self):
        self.buf = None
        self.status = STATUS_COMPLETE


class Piece(object):
    MAX_CHUNK = 16384

    def __init__(self, hash, length, index):
        self.hash = hash
        self.length = length
        self.index = index
        self.chunks = []
        self.status = STATUS_EMPTY

    def prepare(self):
        chunk_count = int(math.ceil(self.length / Piece.MAX_CHUNK))
        for x in xrange(chunk_count):
            chunk = Chunk(x * Piece.MAX_CHUNK)
            self.chunks.append(chunk)

    def complete(self):
        self.chunks = []
        self.status = STATUS_COMPLETE
