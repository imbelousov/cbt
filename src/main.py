#! /usr/bin/python

"""
Console Bit Torrent Client
"""

import doctest
import os

import bcode
import tracker

def main():
    with open("1.torrent", "rb") as file:
        contents = file.read()
    meta = bcode.decode(contents)
    tracker_ = tracker.create(meta)
    if not tracker:
        return
    print tracker_.host

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
