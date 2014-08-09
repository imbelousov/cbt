#! /usr/bin/python
# -*- coding: utf-8 -*-

from BCode import BCode
from Tracker import GetTracker
from Errors import CbtError
from Net import CharToBytes, IntToBytes, BytesToChar, BytesToInt
import os
import hashlib
import time
import threading
import socket
import time

class Peer:
    class PeerError(CbtError):
        pass

    def __init__(self, Meta):
        self.Meta = Meta
        self.PeerId = self.GetId()
        self.InfoHash = self.GetInfoHash()
        self.ListenPort = self.GetPort(6881, 6889)
        self.Tracker = GetTracker(self.Meta)
        self.PieceLength = self.Meta["info"]["piece length"]
        self.PieceHash = self.GetPieceHashes()
        self.PieceCount = len(self.PieceHash)
        self.Peers = []
        self.ActivePeers = []
        self.Files = []
        self.Interval = 0
        self.MinInterval = 0
    
    def StartDownload(self, Path):
        self.StopDownload()
        Info = self.Tracker.Request(
            Event = "started",
            InfoHash = self.InfoHash,
            PeerId = self.PeerId,
            Port = self.ListenPort,
            Uploaded = 0,
            Downloaded = 0,
            Left = 0
        )
        self.Interval = Info["interval"]
        self.MinInterval = Info["min interval"]
        self.Peers = self.GetPeers(Info["peers"])
        self.MakeFiles(Path)
        self.Handshake()
        print self.ActivePeers
        #TODO: Downloading
        #print len(self.Request(self.ActivePeers[0], 0, 0, 10))
    
    def StopDownload(self):
        self.Tracker.Request(
            Event = "stopped",
            InfoHash = self.InfoHash,
            PeerId = self.PeerId,
            Port = self.ListenPort,
            Uploaded = 0,
            Downloaded = 0,
            Left = 0
        )
        for Peer in self.ActivePeers:
            Peer["connection"].close()
        self.ActivePeers = []
    
    def MakeFiles(self, Path):
        def MakeOne(Name, Length):
            Dir = os.sep.join(Name.split(os.sep)[:-1])
            try:
                if not os.path.isdir(Dir):
                    os.makedirs(Dir)
                File = open(Name, "wb")
                File.seek(Length - 1)
                File.write("\0")
                File.close()
                self.Files.append({
                    "path": Name,
                    "length": Length,
                })
            except:
                raise Peer.PeerError("Access denied")
        
        if Path[-1] != os.sep:
            Path += os.sep
        if "files" in self.Meta["info"]:
            """Multiple file mode"""
            for File in self.Meta["info"]["files"]:
                FileLength = File["length"]
                FileName = Path + os.pathsep.join(File["path"])
                MakeOne(FileName, FileLength)
        elif "name" in self.Meta["info"] and "length" in self.Meta["info"]:
            """Single file mode"""
            FileName = Path + self.Meta["info"]["name"]
            FileLength = self.Meta["info"]["length"]
            MakeOne(FileName, FileLength)
        else:
            raise Peer.PeerError("Invalid meta file")
    
    def Handshake(self):
        Data = ""
        self.ActivePeers = []
        ProtocolIdentifier = "BitTorrent protocol"
        Data += CharToBytes(len(ProtocolIdentifier))
        Data += ProtocolIdentifier
        Data += IntToBytes(0)
        Data += IntToBytes(0)
        Data += self.InfoHash
        Data += self.PeerId
        ActivePeersLock = threading.Lock()
        def SayHello(Peer):
            try:
                Connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                Connection.settimeout(2)
                Connection.connect((Peer["ip"], Peer["port"]))
                Connection.sendall(Data)
                Response = Connection.recv(128)
                Connection.close()
                if len(Response) < 49:
                    return
                RemoteProtocolLength = BytesToChar(Response[0])
                RemoteProtocol = Response[1:RemoteProtocolLength+1]
                if RemoteProtocol != "BitTorrent protocol":
                    return
                RemoteInfoHash = Response[RemoteProtocolLength+9:RemoteProtocolLength+29]
                RemotePeerId = Response[RemoteProtocolLength+29:RemoteProtocolLength+49]
                RemotePeerTimestamp = int(time.time())
                ActivePeersLock.acquire()
                self.ActivePeers.append({
                    "ip": Peer["ip"],
                    "port": Peer["port"],
                    "id": RemotePeerId,
                    "timestamp": RemotePeerTimestamp,
                })
                ActivePeersLock.release()
            except:
                pass
        Threads = []
        for Peer in self.Peers:
            RemotePeerThread = threading.Thread(target = SayHello, args = (Peer,))
            Threads.append(RemotePeerThread)
            RemotePeerThread.start()
        for Thread in Threads:
            Thread.join()
    
    def Request(self, Peer, Index, Offset, Length):
        Connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        Connection.connect((Peer["ip"], Peer["port"]))
        Data = ""
        Data += IntToBytes(13)
        Data += "6"
        Data += IntToBytes(Index)
        Data += IntToBytes(Offset)
        Data += IntToBytes(Length)
        Connection.sendall(Data)
        Result = ""
        Connection.close()
        return Result
    
    def GetPeers(self, Raw):
        if type(Raw) == str:
            Peers = []
            for i in xrange(0, len(Raw), 6):
                PeerBytes = Raw[i:i+6]
                PeerIpBytes = PeerBytes[0:4]
                PeerPortBytes = PeerBytes[4:6]
                PeerIp = ".".join([str(ord(c)) for c in PeerIpBytes])
                PeerPort = ord(PeerPortBytes[0])*0x100 + ord(PeerPortBytes[1])
                Peers.append({
                    "ip": PeerIp,
                    "port": PeerPort,
                })
            return Peers
    
    def GetId(self):
        Pid = os.getpid()
        Timestamp = time.time()
        UniqueString = "%s_%s" % (Pid, Timestamp)
        UniqueHash = hashlib.sha1(UniqueString).digest()
        Azareus = "-CB0100-"
        PeerId = Azareus + UniqueHash[len(Azareus):]
        return PeerId
    
    def GetInfoHash(self):
        BCoder = BCode()
        InfoBCode = BCoder.Encode(self.Meta["info"])
        InfoHash = hashlib.sha1(InfoBCode).digest()
        return InfoHash
    
    def GetPort(self, Start, End):
        def CheckPort(Port):
            Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            Result = Sock.connect_ex(('127.0.0.1', Port))
            Sock.close()
            return False if Result == 0 else True
        for Port in xrange(Start, End):
            if CheckPort(Port):
                return Port
        raise Peer.PeerError("Unable to listen any BitTorrent port")
    
    def GetPieceHashes(self):
        Hashes = []
        HashesRaw = self.Meta["info"]["pieces"]
        for i in xrange(0, len(HashesRaw), 20):
            Hashes.append(HashesRaw[i:i+20])
        return Hashes
