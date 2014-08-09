#! /usr/bin/python
# -*- coding: utf-8 -*-

from TrackerRequest import TrackerRequest
from BCode import BCode
import urllib
import urllib2

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
        BCoder = BCode()
        Result = BCoder.Decode(Response)
        return Result