import sys
import time
sys.path.insert(0, "..")

import base
import torrent.file
import tracker.get


class Client(base.BaseClient):
    def open_from_file(self, path):
        self._torrent = torrent.file.TorrentFile(path)
        self._tracker = tracker.get.get(self._torrent.get_trackers())
        if not self._tracker:
            raise RuntimeError("All trackers are unavailable")

