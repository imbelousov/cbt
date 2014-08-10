#! /usr/bin/python

from TrackerRequest import TrackerRequest

__all__ = [
    "UdpTrackerRequest",
]

class UdpTrackerRequest(TrackerRequest):
    def __init__(self, Host, Info):
        super(UdpTrackerRequest, self).__init__(Host, Info)
    
    def Request(self, Event, InfoHash, PeerId, Port, Uploaded, Downloaded, Left):
        return None