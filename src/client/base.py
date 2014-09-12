import sys
import time
sys.path.insert(0, "..")

import torrent.file
import tracker.get


class BaseClient(object):
    def __init__(self):
        self._torrent = None
        self._tracker = None
        self._path = None

    def set_download_path(self, path):
        self._path = path

    def start(self):
        pass

    def stop(self):
        pass
