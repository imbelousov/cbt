#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from bencode import Bencode
from tracker import TrackerRequest

def main():
    File = Bencode()
    File.OpenFromFile("1.torrent")
    Element = File.Decode()
    File.Close()
    Request = TrackerRequest()
    Request.Meta(Element)
    Request.Request("01234567890123456789", 6885)

if __name__ == "__main__":
    main()