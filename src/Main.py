#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from BCode import BCode
from Peer import Peer

def main():
    BCoder = BCode()
    BCoder.OpenFromFile("1.torrent")
    Meta = BCoder.Decode()
    BCoder.Close()
    Me = Peer(Meta)
    Me.StartDownload()

if __name__ == "__main__":
    main()