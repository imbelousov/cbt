#! /usr/bin/python
# -*- coding: utf-8 -*-

from TrackerRequest import TrackerRequest

class UdpTrackerRequest(TrackerRequest):
    def __init__(self, Host, Info):
        super(UdpTrackerRequest, self).__init__(Host, Info)
    
    def Request(self, Event, InfoHash, PeerId, Port, Uploaded, Downloaded, Left):
        return None