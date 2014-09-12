import re
import socket
import sys
import urllib
import urllib2
sys.path.insert(0, "..")

import base
import bcode.decoder


class TCPTracker(base.BaseTracker):
    def __init__(self, url):
        self._url = url
        self._peers = []

    DEFAULT_PORT = 80

    def check(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        pattern = re.compile("^https?://([a-zA-Z0-9.\-]+):?([0-9]*)/?")
        if pattern.match(self._url) is None:
            return False
        splitted = pattern.split(self._url)
        addr = splitted[1]
        port = splitted[2]
        if port:
            port = int(port)
        else:
            port = TCPTracker.DEFAULT_PORT
        try:
            sock.connect((addr, port))
            sock.close()
            result = True
        except (socket.error, socket.timeout):
            result = False
        return result

    def send_start(self):
        #self._request(
        #)
        pass

    def get_peers(self):
        return self._peers[:]

    def _request(self, info_hash, peer_id, port, uploaded, downloaded, left, event):
        sep = "&" if "?" in self._url else "?"
        get = {
            "info_hash": info_hash,
            "peer_id": peer_id,
            "port": port,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": left,
            "compact": 1,
            "event": event
        }
        param = urllib.urlencode(get)
        url = sep.join((self._url, param))
        response = "de"
        try:
            response = urllib2.urlopen(url).read()
        except urllib2.URLError:
            pass
        result = bcode.decoder.decode(response)
        return result
