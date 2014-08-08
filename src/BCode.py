#!/usr/bin/python

from Errors import CbtError
import collections
import os.path
import cStringIO

class BCode():
    class BCodeError(CbtError):
        pass

    def __init__(self):
        self.File = None
        self.Data = None
    
    def OpenFromFile(self, FileName):
        """Makes .torrent file ready to read"""
        self.FileName = FileName
        IsFileExists = os.path.isfile(self.FileName)
        if not IsFileExists:
            raise BCodeError("File does not exist")
        if self.File:
            self.Close()
        self.File = open(self.FileName, "rb")
    
    def OpenFromString(self, String):
        """Makes string stream from string"""
        if self.File:
            self.Close()
        self.File = cStringIO.StringIO()
        self.File.write(String)
        self.File.seek(0)
    
    def OpenFromElement(self, Element):
        """Makes any element ready to encode"""
        if self.File:
            self.Close()
        self.Data = Element
    
    def Decode(self):
        """Converts Bencode to element, generally dictionary"""
        if not self.File:
            raise BCodeError("Cannot read file")
        self.Data = self.ReadElement()
        return self.Data
    
    def Close(self):
        if not self.File:
            if self.Data:
                self.Data = None
            return
        self.File.close()
        self.File = None
    
    def Encode(self, Element=None):
        """Converts element to Bencode string"""
        if Element == None:
            Element = self.Data
        Type = type(Element)
        EncodedString = ""
        if Type in (dict, collections.OrderedDict):
            for Key in Element:
                Value = Element[Key]
                KeyEncoded = self.Encode(Key)
                ValueEncoded = self.Encode(Value)
                EncodedString = "".join((EncodedString, KeyEncoded, ValueEncoded))
            EncodedString = "".join(("d", EncodedString, "e"))
        elif Type == list:
            for Item in Element:
                ItemEncoded = self.Encode(Item)
                EncodedString = "".join((EncodedString, ItemEncoded))
            EncodedString = "".join(("l", EncodedString, "e"))
        elif Type == int:
            EncodedString = "".join(("i", str(Element), "e"))
        elif Type == str:
            EncodedString = "%s%s:%s" % (EncodedString, len(Element), Element)
        return EncodedString
    
    def ReadNumber(self):
        """Format: i<Digits>e"""
        Type = self.ReadByte()
        if Type != "i":
            raise BCodeError("Element is not a number")
        Number = self.ReadDigits()
        self.ReadByte()
        return Number
    
    def ReadByteArray(self):
        """Format: <Array Size>:<Array Bytes>"""
        Type = self.ReadByte(True)
        if not Type in self.DigitsGenerator():
            raise BCodeError("Element is not a byte array")
        Size = self.ReadDigits()
        self.ReadByte()
        ByteArray = ""
        for x in xrange(Size):
            Byte = self.ReadByte()
            ByteArray += Byte
        return ByteArray
    
    def ReadList(self):
        """Format: l<Elements>e"""
        Type = self.ReadByte()
        if Type != "l":
            raise BCodeError("Element is not a list")
        List = []
        while True:
            Byte = self.ReadByte(True)
            if Byte == "e":
                break
            Element = self.ReadElement()
            List.append(Element)
        self.ReadByte()
        return List
    
    def ReadDictionary(self):
        """Format: d<Dictionary Elements>e
           Element: <Byte Array><Element>"""
        Type = self.ReadByte()
        if Type != "d":
            raise BCodeError("Element is not a dictionary")
        Dictionary = collections.OrderedDict()
        while True:
            Byte = self.ReadByte(True)
            if Byte == "e":
                break
            Key = self.ReadByteArray()
            Value = self.ReadElement()
            Dictionary[Key] = Value
        self.ReadByte()
        return Dictionary
    
    def ReadElement(self):
        """Automatic type recognizing"""
        Type = self.ReadByte(True)
        if Type == "i":
            Number = self.ReadNumber()
            return Number
        elif Type == "l":
            List = self.ReadList()
            return List
        elif Type == "d":
            Dictionary = self.ReadDictionary()
            return Dictionary
        elif Type in self.DigitsGenerator():
            ByteArray = self.ReadByteArray()
            return ByteArray
        else:
            return None
    
    def ReadByte(self, quiet=False):
        Byte = self.File.read(1)
        if quiet:
            self.File.seek(-1, 1)
        return Byte
    
    def ReadDigits(self):
        Digits = ""
        while True:
            Byte = self.ReadByte()
            if Byte in self.DigitsGenerator():
                Digits += Byte
            else:
                self.File.seek(-1, 1)
                break
        Digits = int(Digits)
        return Digits
    
    def DigitsGenerator(self):
        for x in xrange(10):
            yield str(x)
        yield "-"
