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
        self._Data = self._ReadElement()
        return self._Data
        
    def _ReadNumber(self):
        """Format: i<Digits>e"""
        return 0

    def _ReadByteArray(self):
        """Format: <Array Size>:<Array Bytes>"""
        try:
            Byte = ""
            Size = ""
            while Byte != ":":
                Size += Byte
                Byte = self._ReadByte()
            Size = int(Size)
            ByteArray = ""
            for i in xrange(Size):
                Byte = self._ReadByte()
                ByteArray += Byte
            return ByteArray
        except:
            return ""

    def _ReadList(self):
        """Format: l<Elements>e"""
        try:
            Type = self._ReadByte()
            if Type != "l":
                raise Exception()
        except:
            return []

    def _ReadDictionary(self):
        """Format: d<Dictionary Elements>e
           Element: <Byte Array><Element>"""
        try:
            Type = self._ReadByte()
            if Type != "d":
                raise Exception()
            Dictionary = {}
            ByteArray = self._ReadByteArray()
            Element = self._ReadElement()
            if Element == False:
                raise Exception()
            Dictionary[ByteArray] = Element
            return Dictionary
        except:
            return {}

    def _ReadElement(self):
        """Automatic type recognizing"""
        Type = self._ReadByte()
        self._ReturnCursor()
        if Type == "i":
            Number = self._ReadNumber()
            return Number
        elif Type == "l":
            List = self._ReadList()
            return List
        elif Type == "d":
            Dictionary = self._ReadDictionary()
            return Dictionary
        elif Type in self._DigitsGenerator():
            ByteArray = self._ReadByteArray()
            return ByteArray
        return None

    def _ReadByte(self):
        return self._File.read(1)

    def _ReturnCursor(self):
        self._File.seek(-1, 1)
    
    def _DigitsGenerator(self):
        return [str(x) for x in xrange(10)]