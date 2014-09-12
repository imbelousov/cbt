__all__ = ["BaseTorrent"]


class BaseTorrent(object):
    def __init__(self):
        # List of tuples (File length <int>, File path <str>)
        self._files = []
        # 20-byte SHA1 hash
        self._hash = ""
        # List of 20-byte SHA1 hashes
        self._piece_hashes = []
        # Integer
        self._piece_length = 0
        # List of URLs
        self._trackers = []

    def get_files(self):
        return self._files

    def get_hash(self):
        return self._hash

    def get_piece_length(self):
        return self._piece_length

    def get_piece_count(self):
        return len(self._piece_hashes)

    def get_piece_hash(self, index):
        if 0 <= index < self.get_piece_count():
            return self._piece_hashes[index]
        else:
            return False

    def get_trackers(self):
        return self._trackers
