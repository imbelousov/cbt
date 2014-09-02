#!/usr/bin/python2

import os
import sys

import torrent


def main(argv):
    argc = len(argv)
    if argc == 0 or argc > 2:
        print "Syntax: cbt <.torrent file> [<download path>]"
        return
    torrent_path = argv[0]
    if argc == 2:
        download_path = argv[1]
    else:
        download_path = os.getcwd()

    print "Starting..."
    try:
        t = torrent.Torrent(torrent_path, download_path)
    except IOError:
        print "Invalid .torrent file"
        return
    t.stop()
    try:
        t.start()
    except WindowsError:
        print "Permission denied"
        return
    print "Started"
    torrent.main_loop()
    print "Stopping..."
    t.stop()


if __name__ == "__main__":
    main(sys.argv[1:])
