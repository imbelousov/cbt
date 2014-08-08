#!/usr/bin/python

from BCode import BCode
from Tracker import GetTracker
from Errors import CbtError
import os
import hashlib
import time
import threading
import socket

class Peer:
    class PeerError(CbtError):
        pass

    def __init__(self, Meta):
        self.Meta = Meta
        self.PeerId = self.GetId()
        self.InfoHash = self.GetInfoHash()
        self.ListenPort = self.GetPort(6881, 6889)
        self.Tracker = GetTracker(self.Meta)
        self.Peers = []
        self.Interval = 0
        self.MinInterval = 0
    
    def StartDownload(self):
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
        self.MakeFiles(r"D:\Tests")
        return self.Peers
    
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
    
    def MakeFiles(self, Path):
        if "files" in self.Meta["info"]:
            for File in self.Meta["info"]["files"]:
                if Path[-1] != os.sep:
                    Path += os.sep
                FileLength = File["length"]
                FileName = Path + os.pathsep.join(File["path"])
                FileDir = os.sep.join(FileName.split(os.sep)[:-1])
                try:
                    if not os.path.isdir(FileDir):
                        os.makedirs(FileDir)
                    File = open(FileName, "wb")
                    File.seek(FileLength - 1)
                    File.write("\0")
                except:
                    raise PeerError("Access denied")
                finally:
                    File.close()
    
    def GetPeers(self, Raw):
        if type(Raw) == str:
            Peers = []
            for i in xrange(0, len(Raw), 6):
                PeerBytes = Raw[i:i+6]
                PeerIpBytes = PeerBytes[0:4]
                PeerPortBytes = PeerBytes[4:6]
                PeerIp = ".".join([str(ord(c)) for c in PeerIpBytes])
                PeerPort = ord(PeerPortBytes[0])*0x100 + ord(PeerPortBytes[1])
                Peers.append({"Ip": PeerIp, "Port": PeerPort})
            return Peers
    
    def GetId(self):
        Pid = os.getpid()
        Timestamp = time.time()
        UniqueString = "%s_%s" % (Pid, Timestamp)
        PeerId = hashlib.sha1(UniqueString).digest()
        return PeerId
    
    def GetInfoHash(self):
        BCoder = BCode()
        BCoder.OpenFromElement(self.Meta["info"])
        InfoBCode = BCoder.Encode()
        BCoder.Close()
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
        raise PeerError("Unable to listen any BitTorrent port")
    
"""    def __init__(self):
        self.Peers = []
        self.PeerId = None
        self.Port = None
        self.TakePort()
    
    def GetId(self):
        if self.PeerId:
            return self.PeerId
        Pid = os.getpid()
        Timestamp = time.time()
        UniqueString = "%s_%s" % (Pid, Timestamp)
        self.PeerId = hashlib.sha1(UniqueString).digest()
        return self.PeerId
    
    def TakePort(self):
        def CheckPort(Port):
            Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            Result = Sock.connect_ex(('127.0.0.1', Port))
            Sock.close()
            return False if Result == 0 else True
        
        Start = 6881
        Range = 9
        for Port in range(Start, Start + Range):
            if CheckPort(Port):
                self.Port = Port
                break
            else:
                self.Port = None
        if not self.Port:
            raise RuntimeError("Unable to listen any BitTorrent port")
        self.ServerThread = threading.Thread(target = self.StartServer, args = ())
        # TODO
        #self.ServerThread.start()
    
    def StartServer(self):
        self.IncomingSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IncomingSock.bind(("0.0.0.0", self.Port))
        self.IncomingSock.listen(32)
        while True:
            PeerConn, PeerAddr = self.IncomingSock.accept()
            threading.Thread(target = self.ConnectionHandler, args = (PeerConn, PeerAddr)).start()
    
    def ConnectionHandler(self, PeerConn, PeerAddr):
        print "Connected", PeerAddr
        PeerConn.close()
    
    def InitPeersList(self, PeersList):
        if type(PeersList) == str:
            self.InitPeersListFromBytes(PeersList)
    
    def InitPeersListFromBytes(self, Bytes):
        def BytesToChars(Bytes):
            for Byte in Bytes:
                yield str(ord(Byte))
        
        def BytesToShort(Bytes):
            return ord(Bytes[0])*0x100 + ord(Bytes[1])
        
        self.Peers = []
        for i in xrange(0, len(Bytes), 6):
            IpBytes = Bytes[i:i+4]
            PortBytes = Bytes[i+4:i+6]
            Ip = []
            for Byte in IpBytes:
                Ip.append(str(ord(Byte)))
            Ip = ".".join(BytesToChars(IpBytes))
            Port = BytesToShort(PortBytes)
            self.Peers.append({"Ip": Ip, "Port": Port})
"""