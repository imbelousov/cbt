import time


class Request(object):
    def __init__(self, node, piece, chunk):
        self.node = node
        self.piece = piece
        self.chunk = chunk
        self.started_at = time.time()
