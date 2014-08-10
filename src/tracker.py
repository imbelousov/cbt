#! /usr/bin/python

import abc
import urllib
import re
import socket

import bcode

__all__ = ["create"]

class Tracker(object):
    __metaclass__ = abc.ABCMeta

    DEFAULT_PORT = None

    def __init__(self, host):
        self.host = host

    @abc.abstractmethod
    def request(self, info_hash, peer_id, my_port, uploaded, downloaded, left, event):
        pass

    def is_available(self):
        pattern = re.compile("^[a-z]+://([a-z0-9.\-]+):?([0-9]*)")
        info = pattern.split(self.host)
        address = info[1]
        port = info[2]
        try:
            port = int(port)
        except:
            port = self.DEFAULT_PORT
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((address, port))
            sock.close()
            return True
        except:
            return False


class HTTPTracker(Tracker):
    DEFAULT_PORT = 80

    def request(self, info_hash, peer_id, my_port, uploaded, downloaded, left, event):
        url = self.host
        sep = "?"
        if sep in url:
            sep = "&"
        get_dict = {}
        get_dict.update({
            "info_hash": self.info_hash,
            "peer_id": peer_id,
            "port": my_port,
            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": left,
            "compact": 1,
            "event": event
        })
        get = urllib.urlencode(get_dict)
        url = "".join((url, sep, get))
        try:
            response = urllib2.urlopen(url).read()
            element = bcode.decode(response)
        except ValueError:
            element = None
        return element


class UDPTracker(Tracker):
    DEFAULT_PORT = 2710

    def request(self, info_hash, peer_id, my_port, uploaded, downloaded, left, event):
        return None


def create(meta):
    """Returns an instance of appropriate tracker class"""
    tracker_types = {
        "http": HTTPTracker,
        "https": HTTPTracker,
        "udp": UDPTracker
    }
    trackers = []
    if "announce" in meta:
        trackers.append(meta["announce"])
    if "announce-list" in meta:
        for item in meta["announce-list"]:
            trackers.append(item[0])
    for url in trackers:
        protocol = url.split("://")[0]
        if protocol not in tracker_types:
            continue
        tracker = tracker_types[protocol](url)
        if tracker.is_available():
            return tracker
    return None
