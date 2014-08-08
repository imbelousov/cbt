#!/usr/bin/python

from HttpTrackerRequest import HttpTrackerRequest
from UdpTrackerRequest import UdpTrackerRequest

def GetTracker(Meta):
    def GetProtocol(Url):
        return Url.split("://")[0]
    
    def CheckAnnouncer(Url):
        Protocol = GetProtocol(Url)
        try:
            if Protocol == "http":
                return HttpTrackerRequest(Url)
            elif Protocol == "udp":
                return UdpTrackerRequest(Url)
        except:
            return False
    
    if "announce" in Meta:
        Tracker = CheckAnnouncer(Meta["announce"])
        if Tracker:
            return Tracker
    if "announce-list" in Meta:
        AnnounceList = Meta["announce-list"]
        for Announce in AnnounceList:
            Announce = Announce[0]
            Tracker = CheckAnnouncer(Announce)
            if Tracker:
                return Tracker
    return None