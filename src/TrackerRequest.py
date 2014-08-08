#!/usr/bin/python

class TrackerRequest():
    __metaclass__ = abc.ABCMeta

    def __init__(self, Host):
        self.Host = Host
    
    @abc.abstractmethod
    def Request(self):
        """Communication with tracker"""
        pass
