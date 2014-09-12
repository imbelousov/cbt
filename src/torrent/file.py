import hashlib
import os
import sys
sys.path.insert(0, "..")

import base
import bcode.decoder
import bcode.encoder

__all__ = ["Torrent"]


class TorrentFile(base.BaseTorrent):
    def __init__(self, path):
        super(TorrentFile, self).__init__()
        self._open(path)

    def _open(self, path):
        with open(path, "rb") as f:
            bencode = f.read()
        meta = bcode.decoder.decode(bencode)
        try:
            # Calc info hash
            info = bcode.encoder.encode(meta["info"])
            self._hash = hashlib.sha1(info).digest()
            # Make files list
            self._files = []
            if "files" in meta["info"]:
                for file_ in meta["info"]["files"]:
                    self._files.append((file_["length"], os.sep.join(file_["path"])))
            else:
                self._files.append((meta["info"]["length"], meta["info"]["name"]))
            # Make piece hashes list
            piece_hashes_raw = meta["info"]["pieces"]
            for x in xrange(0, len(piece_hashes_raw), 20):
                self._piece_hashes.append(piece_hashes_raw[x:x+20])
            # Get length of piece
            self._piece_length = meta["info"]["piece length"]
            # Make list of trackers
            self._trackers = [meta["announce"]]
            if "announce-list" in meta:
                for tracker in meta["announce-list"]:
                    if tracker[0] not in self._trackers:
                        self._trackers.append(tracker[0])
        except KeyError:
            raise IOError("Invalid .torrent file")
