import os

__all__ = ["File"]


class File(object):
    """Each file in a torrent is represented as File object.

    Attributes:

        intorrent_path:
            Path inside the torrent folder.
            string or iterable

        download_path:
            Torrent folder path.

        size:
            Size of the file

        offset:
            Index of the first byte of the file in the whole torrent

    Methods:

        create():
            Allocate physical memory on disk for the file.

    """

    def __init__(self, intorrent_path, download_path, size, offset):
        if type(intorrent_path) is str:
            intorrent_path = intorrent_path.split(os.sep)
        download_path = os.path.abspath(download_path).split(os.sep)
        full_path = download_path + intorrent_path
        self.name = os.sep.join(full_path)
        self.path = os.sep.join(full_path[:-1])
        self.size = size
        self.offset = offset

    def create(self):
        """Allocate physical memory on disk for the file.
        There will be no changes on disk if this file
        already exists and its size coincides.
        There is no guarantee that the file consists of zeros.

        """
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        if os.path.isfile(self.name):
            if os.path.getsize(self.name) == self.size:
                return
        with open(self.name, "wb") as f:
            f.seek(self.size - 1, 1)
            f.write("\0")
