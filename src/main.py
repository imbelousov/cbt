#!/usr/bin/python2

import torrent


def main():
    t = torrent.Torrent("data\\2.torrent", "data\\download")
    t.stop()
    print "Connecting to peers..."
    t.start()
    print "Started"
    try:
        while True:
            t.message()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
