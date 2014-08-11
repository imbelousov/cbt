#! /usr/bin/python

"""
Console Bit Torrent Client
"""

import doctest
import os

import peer
import tracker

def main():
    me = peer.Peer()
    with open("1.torrent", "rb") as file:
        contents = file.read()
    me.add_torrent(contents, "D:\\Tests")
    me.start(0)

def test():
    tests = ["test_bcode.txt"]
    path = ["..", "tests"]
    # Reserved for test name
    path.append("")
    for test in tests:
        path[-1] = test
        file_name = os.sep.join(path)
        doctest.testfile(file_name)
    
if __name__ == "__main__":
    test()
    main()
