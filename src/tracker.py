#! /usr/bin/python

import urllib

import bcode

__all__ = ["create"]

class Tracker(object):
    def __init__(self, host, info_hash):
        self.host = host
        self.info_hash = info_hash
    
    def request(self):
        pass
    
    def is_available(self):
        return False


class HTTPTracker(Tracker):
    def request(self, peer_id, my_port, uploaded, downloaded, left, event):
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
        response = urllib2.urlopen(url).read()
        try:
            element = bcode.decode(response)
        except ValueError:
            element = None
        return element


def check(url):
    """Check if tracker is available"""
    protocol = url.split("://")[0]
    try:
        
    except:
        return False

def create(meta):
    """Returns an instance of appropriate tracker class"""
    pass
    