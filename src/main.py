#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from bencode import Bencode

def main():
    Object = Bencode()
    Object.Open("1.torrent")
    print Object.Read()

if __name__ == "__main__":
    main()