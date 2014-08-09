#! /usr/bin/python

"""
Console Bit Torrent Client
"""

import doctest
import os

from BCode import BCode
from Peer import Peer

def Main():
    Meta = BCode().DecodeFile("2.torrent")
    Me = Peer()
#    Me.StartDownload(r"D:\Tests")

def Test():
    Tests = [
        "BCodeTests.txt",
    ]
    Path = [
        "..",
        "tests",
    ]
    for Test in Tests:
        _Path = Path[:]
        _Path.append(Test)
        _PathStr = os.sep.join(_Path)
        doctest.testfile(_PathStr)
    
if __name__ == "__main__":
    Test()
    Main()
