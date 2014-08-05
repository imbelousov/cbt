#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from bencode import Bencode

def main():
    File = Bencode()
    File.OpenFromFile("1.torrent")
    Element = File.Decode()
    File.Close()
    File.OpenFromElement(Element)
    BencodeString = File.Encode()
    File.Close()
    open("2.torrent", "wb").write(BencodeString)

if __name__ == "__main__":
    main()