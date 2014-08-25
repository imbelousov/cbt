#!/usr/bin/python2

import torrent


def main():
    t = torrent.Torrent("data\\2.torrent", "data\\download")
    t.stop()
    print "Connecting to peers..."
    t.start()
    print "Started"
    torrent.main_loop()
    print "Stopping..."
    t.stop()

if __name__ == "__main__":
    main()
