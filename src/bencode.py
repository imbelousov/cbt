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
        """Converts Bencode file contents to element, generally dictionary"""
        if not self._File:
            return None
        self._Data = self._ReadElement()
        return self._Data
        
    def _ReadNumber(self):
        """Format: i<Digits>e"""
        try:
            Type = self._ReadByte()
            if Type != "i":
                raise RuntimeError("Element is not a number")
            Number = self._ReadDigits()
            self._ReadByte()
            return Number
        except:
            return 0

    def _ReadByteArray(self):
        """Format: <Array Size>:<Array Bytes>"""
        try:
            Type = self._ReadByte(True)
            if not Type in self._DigitsGenerator():
                raise RuntimeError("Element is not a byte array")
            Size = self._ReadDigits()
            self._ReadByte()
            ByteArray = ""
            for i in xrange(Size):
                try:
                    Byte = self._ReadByte()
                    ByteArray += Byte
                    print len(Byte)
                except:
                    print "Err: %d" % i
            if Size == 11740:
                print "%d (%d)" % (Size, len(ByteArray))
            return ByteArray
        except:
            return ""

    def _ReadList(self):
        """Format: l<Elements>e"""
        try:
            Type = self._ReadByte()
            if Type != "l":
                raise RuntimeError("Element is not a list")
            List = []
            while True:
                Byte = self._ReadByte(True)
                if Byte == "e":
                    break
                Element = self._ReadElement()
                List.append(Element)
            self._ReadByte()
            return List
        except:
            return []

    def _ReadDictionary(self):
        """Format: d<Dictionary Elements>e
           Element: <Byte Array><Element>"""
        try:
            Type = self._ReadByte()
            if Type != "d":
                raise RuntimeError("Element is not a dictionary")
            Dictionary = {}
            # TODO: delete this
            max = 100
            while True:
                Byte = self._ReadByte(True)
                if Byte == "e":
                    break
                Key = self._ReadByteArray()
                Value = self._ReadElement()
                Dictionary[Key] = Value
                max -= 1
                if max == 0:
                    break
            self._ReadByte()
            return Dictionary
        except:
            return {}

    def _ReadElement(self):
        """Automatic type recognizing"""
        Type = self._ReadByte(True)
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

    def _ReadByte(self, quiet=False):
        Byte = self._File.read(1)
        if quiet:
            self._File.seek(-1, 1)
        return Byte

    def _ReadDigits(self):
        Digits = ""
        try:
            while True:
                Byte = self._ReadByte()
                if Byte in self._DigitsGenerator():
                    Digits += Byte
                else:
                    self._File.seek(-1, 1)
                    break
            Digits = int(Digits)
        except:
            Digits = 0
        return Digits

    def _DigitsGenerator(self):
        return [str(x) for x in xrange(10)]