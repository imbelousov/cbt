#!/usr/bin/python2

import time

import client


def main():
    c = client.Client()
    c.append("data\\2.torrent", "data\\download")
    c.stop()
    c.start()
    time.sleep(5)
    c.stop()

if __name__ == "__main__":
    main()