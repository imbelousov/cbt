#!/usr/bin/python

from bencode import Bencode
import collections
import hashlib
import urllib

class TrackerRequest():
    def __init__(self):
        self._Meta = {}

    def Meta(self, Element):
        """Saves .torrent meta data"""
        if not type(Element) in (dict, collections.OrderedDict):
            return
        self._Meta = Element

    def Request(self, PeerId, Port):
        """Compiles and sends request to tracker using GET method"""
        Get = collections.OrderedDict()    # All variables in dictionary
        Bencoder = Bencode()
        Bencoder.OpenFromElement(self._Meta["info"])    # "info" dictionary hash needed only
        InfoBencode = Bencoder.Encode()
        Bencoder.Close()
        
        # info_hash
        InfoHash = hashlib.sha1(InfoBencode).digest()
        InfoHash = urllib.quote_plus(InfoHash)
        Get["info_hash"] = InfoHash
        # peer_id
        Get["peer_id"] = urllib.quote_plus(PeerId)
        # port
        Get["port"] = int(Port)
        # TODO
        Get["uploaded"] = 0
        Get["downloaded"] = 0
        Get["left"] = 0
        # Compact mode ON
        Get["compact"] = 1
        # TODO: Event
        Get["event"] = "started"
        
        # Compiling URL
        Url = "%s?" % self._Meta["announce-list"][0][0]
        for Key in Get:
            Url = "%s%s=%s&" % (Url, Key, Get[Key])
        print Url