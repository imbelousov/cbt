#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from BCode import BCode
from HttpTrackerRequest import HttpTrackerRequest
from PeerId import GetPeerId
from Tracker import GetTracker

def main():
    File = BCode()
    File.OpenFromFile("1.torrent")
    Meta = File.Decode()
    File.Close()
    Tracker = GetTracker(Meta)
    if not Tracker:
        print "Unable to connect to tracker"
    Tracker.Request("stopped")
    print Tracker.Request("started")

if __name__ == "__main__":
    main()