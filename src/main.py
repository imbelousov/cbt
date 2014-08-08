#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from BCode import BCode
from HttpTrackerRequest import HttpTrackerRequest
from PeerId import GetPeerId

def main():
    File = BCode()
    File.OpenFromFile("1.torrent")
    Element = File.Decode()
    File.Close()
    Client = HttpTrackerRequest(Element["announce"], Element["info"])
    print Client.Request("stopped")

if __name__ == "__main__":
    main()