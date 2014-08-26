import urllib
import urllib2
import re
import socket

import bcode

__all__ = ["get"]


class Tracker(object):
    """Base BitTorrent tracker class.
    Doesn't fully implement network communication.

    """

    DEFAULT_PORT = None

    def __init__(self, host):
        self.host = host

    def request(self, hash, id, port, uploaded, downloaded, left, event):
        """Overridden methods should return a dictionary of params or None."""
        return None

    def is_available(self):
        """Try to connect to tracker through TCP/IP. Return True if connection
        successful and False if not.

        """
        pattern = re.compile("^[a-z]+://([a-z0-9.\-]+):?([0-9]*)/?")
        info = pattern.split(self.host)
        address = info[1]
        port = info[2]
        result = True
        try:
            port = int(port)
        except ValueError:
            port = self.DEFAULT_PORT
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            sock.connect((address, port))
        except socket.timeout:
            result = False
        finally:
            sock.close()
        return result


class HTTPTracker(Tracker):
    """Regular BitTorrent tracker class.
    Requests are sent through HTTP messages using GET method.
    Tracker response is plain/text bencoded or empty string.

    """

    DEFAULT_PORT = 80

    def request(self, hash, id, port, uploaded, downloaded, left, event):
        url = self.host
        sep = "?"
        if sep in url:
            sep = "&"
        get_dict = {}
        get_dict.update({
            "info_hash": hash,
            "peer_id": id,
            "port": port,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": left,
            "compact": 1,
            "event": event
        })
        param = urllib.urlencode(get_dict)
        url = "".join((url, sep, param))
        response = ""
        try:
            response = urllib2.urlopen(url).read()
        except urllib2.URLError:
            pass
        result = bcode.decode(response)
        return result


class UDPTracker(Tracker):
    """eXtended BitTorrent Tracker class.
    Requests are sent through UDP datagrams.

    """

    DEFAULT_PORT = 2710

    def request(self, hash, id, port, uploaded, downloaded, left, event):
        # TODO: XBTT Tracker request
        return ""


def get(url_list):
    """Returns an instance of appropriate tracker class.
    Try to connect to trackers in url_list until one of them
    does not respond.

    Args:
        url_list: a list of full URLs of all valid trackers for the torrent.

    Returns:
        An object of appropriate subclass of Tracker that sends requests to
        the first available tracker in the list or None if there is no
        available tracker.

    """
    tracker_classes = {
        "http": HTTPTracker,
        "https": HTTPTracker,
        "udp": UDPTracker
    }
    tracker = None
    for url in url_list:
        protocol = url.split("://")[0]
        if protocol not in tracker_classes:
            continue
        TrackerClass = tracker_classes[protocol]
        tracker = TrackerClass(url)
        if tracker.is_available():
            break
    return tracker
