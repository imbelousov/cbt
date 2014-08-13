#! /usr/bin/python

"""
Console Bit Torrent Client
"""

import doctest
import os

import client

def main():
    c = client.Client()
    c.append("2.torrent", "D:\\Tests")
    c.get(0).stop()
    c.get(0).start()

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
