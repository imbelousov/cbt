import os

class Bencode():
    def __init__(self):
        self._File = None

    def Open(self, FileName):
        self._FileName = FileName
        IsFileExists = os.path.isfile(self._FileName)
        if not IsFileExists:
            return False
        self._File = open(self._FileName)
        return True

    def Read(self):
        """Converts Bencode file contents to dictionary"""
        if not self._File:
            return {}
        FileSize = os.path.getsize(self._FileName)
        Byte = self._File.read(1)
"""        if Byte != "d":
            raise RuntimeError("Invalid file")
        self._Data = {}
        for i in xrange(FileSize):"""
        
