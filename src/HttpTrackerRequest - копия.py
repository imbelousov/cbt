#! /usr/bin/python

import urllib
import urllib2

from BCode import BCode
from TrackerRequest import TrackerRequest

__all__ = [
    "HttpTrackerRequest",
]

class HttpTrackerRequest(TrackerRequest):
    def __init__(self, Host):
        super(HttpTrackerRequest, self).__init__(Host)
    
    def Request(self, Event, InfoHash, PeerId, Port, Uploaded, Downloaded, Left):
        Url = self.Host
        if not "?" in Url:
            UrlSeparator = "?"
        else:
            UrlSeparator = "&"
        Url += UrlSeparator
        Get = {}
        Get["info_hash"] = InfoHash
        Get["peer_id"] = PeerId
        Get["port"] = Port
        Get["uploaded"] = Uploaded
        Get["downloaded"] = Downloaded
        Get["left"] = Left
        Get["compact"] = 1
        Get["event"] = Event
        UrlParams = urllib.urlencode(Get)
        Url += UrlParams
        Response = urllib2.urlopen(Url).read()
        try:
            Result = BCode().Decode(Response)
        except:
            Result = None
        return Result