#!/usr/bin/python2

import time

import peer


def on_recv(node, buf):
    print buf


def main():
    p = peer.Peer()
    p.append_node("127.0.0.1", 8888)
    p.on_recv(on_recv)
    p.connect_all()
    try:
        while True:
            p.message()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
