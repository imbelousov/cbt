#! /usr/bin/python

import hashlib
import os
import time
import socket
import threading

import torrent
import net

__all__ = ["Peer"]

class Peer(object):
    def __init__(self):
        self.ver = "-CB0100-"
        self.torrents = []
        self.peer_id = self.get_id()
        self.port = self.get_port()

    def get_id(self):
        pid = str(os.getpid())
        timestamp = str(time.time())
        unique_string = "_".join((pid, timestamp))
        unique_hash = hashlib.sha1(unique_string).digest()
        return "".join((self.ver, unique_hash[len(self.ver):]))

    def get_port(self):
        def check(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result != 0

        r = xrange(6881, 6890)
        for port in r:
            if check(port):
                return port
        raise RuntimeError("Unable to listen any BitTorrent port")

    def add_torrent(self, contents, path=None):
        if path is None:
            path = "."
        t = torrent.Torrent(contents, path)
        self.torrents.append(t)

    def get_torrent(self, index):
        tl = len(self.torrents)
        if tl == 0 or index < -1 or index >= tl:
            raise IndexError("Torrent with this index does not exist")
        return self.torrents[index]

    def start(self, index=-1):
        self.stop()
        t = self.get_torrent(index)
        for file in t.files:
            try:
                if not os.path.isdir(file["path"]):
                    os.makedirs(file["path"])
                with open(file["name"], "wb") as file_d:
                    file_d.seek(file["length"] - 1)
                    file_d.write("\0")
            except:
                raise IOError("Access denied")
        response = t.tracker.request(
            info_hash = t.info_hash,
            peer_id = self.peer_id,
            my_port = self.port,
            uploaded = 0,
            downloaded = 0,
            left = 0,
            event = "started"
        )
        t.peers = []
        if type(response["peers"]) is str:
            g = [
                response["peers"][x:x+6]
                for x
                in xrange(0, len(response["peers"]), 6)
            ]
            for bytes in g:
                peer_ip = ".".join([str(ord(byte)) for byte in bytes[0:4]])
                peer_port = ord(bytes[4])*0x100 + ord(bytes[5])
                t.peers.append({
                    "ip": peer_ip,
                    "port": peer_port
                })
        self.handshake(index)
        for peer in t.active_peers:
            print peer

    def stop(self, index=-1):
        t = self.get_torrent(index)
        t.tracker.request(
            info_hash = t.info_hash,
            peer_id = self.peer_id,
            my_port = self.port,
            uploaded = 0,
            downloaded = 0,
            left = 0,
            event = "stopped"
        )

    def handshake(self, index):
        t = self.get_torrent(index)
        t.active_peers = []
        h_threads = []
        h_lock = threading.Lock()
        hello = "".join((
            chr(19),
            "BitTorrent protocol",
            net.uint64_chr(0),
            t.info_hash,
            self.peer_id
        ))
        def say_hello(ip, port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, port))
                sock.sendall(hello)
                response = sock.recv(128)
                if len(response) < 49:
                    return
                r_proto_len = ord(response[0])
                r_proto = response[1:r_proto_len+1]
                if r_proto != "BitTorrent protocol":
                    return
                r_info_hash = response[r_proto_len+9:r_proto_len+29]
                r_peer_id = response[r_proto_len+29:r_proto_len+49]
                r_timestamp = int(time.time())
                h_lock.acquire()
                t.active_peers.append({
                    "ip": ip,
                    "port": port,
                    "peer_id": r_peer_id,
                    "timestamp": r_timestamp
                })
            except:
                pass
            finally:
                if h_lock.locked():
                    h_lock.release()

        for peer in t.peers:
            thread = threading.Thread(target = say_hello, args = (peer["ip"], peer["port"]))
            thread.start()
            h_threads.append(thread)
        for thread in h_threads:
            thread.join()
