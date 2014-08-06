#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from bencode import Bencode
from tracker import TrackerRequest
from peerid import GetPeerId

def main():
    File = Bencode()
    File.OpenFromFile("1.torrent")
    Element = File.Decode()
    File.Close()
    Request = TrackerRequest()
    Request.Meta(Element)
    Request.Request(GetPeerId(), 6881)

if __name__ == "__main__":
    main()