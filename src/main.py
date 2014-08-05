#!/usr/bin/python

"""
Console Bit Torrent Client
"""

import sys
from bencode import Bencode

def main():
    sys.dont_write_bytecode = True
    Object = Bencode()
    Object.Open("1.torrent")
#    Object.Open("test.torrent")
    dict = Object.Read()
    for key in dict:
        print "%s : %s" % (key, dict[key])

if __name__ == "__main__":
    main()