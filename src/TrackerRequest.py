#!/usr/bin/python

from BCode import BCode
import hashlib
import socket
import abc

class TrackerRequest():
    __metaclass__ = abc.ABCMeta

    def __init__(self, Host, Info):
        self.Info = Info
        self.Host = Host
        self.Port = None
    
    def Start(self):
        self.SendRequest()
    
    def GetInfoHash(self):
        Coder = BCode()
        Coder.OpenFromElement(self.Info)
        InfoBCode = Coder.Encode()
        Coder.Close()
        InfoHash = hashlib.sha1(InfoBCode).digest()
        return InfoHash
    
    def GetPort(self):
        def CheckPort(Port):
            Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            Result = Sock.connect_ex(('127.0.0.1', Port))
            Sock.close()
            return False if Result == 0 else True
                    
        if self.Port:
            if CheckPort(self.Port):
                return self.Port
        Start = 6881
        Range = 9
        for Port in range(Start, Start + Range):
            if CheckPort(Port):
                self.Port = Port
                return Port
        raise RuntimeError("Unable to listen any BitTorrent port")
    
    @abc.abstractmethod
    def Request(self):
        """Communication with tracker"""
        pass

