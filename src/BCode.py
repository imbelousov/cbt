#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Bencode encoding/decoding class
Usage: BCode().Encode(Element)
       BCode().Decode(EncodedString)
       BCode().DecodeFile(FileName)
Supported element types:
- int
- str
- list
- dict / OrderedDict
"""

from Errors import CbtError
import collections
import os.path
import cStringIO

class BCode():
    class BCodeError(CbtError):
        pass

    def __init__(self):
        self.File = None
    
    def Decode(self, EncodedString):
        """Converts Bencode to element, generally dictionary"""
        if type(EncodedString) != str:
            return None
        if self.File:
            self.File.close()
        self.File = cStringIO.StringIO()
        self.File.write(EncodedString)
        self.File.seek(0)
        Element = self.ReadElement()
        self.File.close()
        self.File = None
        return Element
    
    def DecodeFile(self, FileName):
        """Converts .torrent file contents to element"""
        IsFileExists = os.path.isfile(FileName)
        if not IsFileExists:
            raise BCode.BCodeError("File does not exist")
        if self.File:
            self.File.close()
        try:
            self.File = open(FileName, "rb")
        except:
            raise BCode.BCodeError("Access denied")
        Element = self.ReadElement()
        self.File.close()
        self.File = 0
        return Element
    
    def Encode(self, Element):
        """Converts element to Bencode string"""
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
            raise BCode.BCodeError("Element is not a number")
        Number = self.ReadDigits()
        while True:
            Byte = self.ReadByte()
            if Byte == "e":
                break
        return Number
    
    def ReadByteArray(self):
        """Format: <Array Size>:<Array Bytes>"""
        Type = self.ReadByte(True)
        if not Type in self.DigitsGenerator():
            raise BCode.BCodeError("Element is not a byte array")
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
            raise BCode.BCodeError("Element is not a list")
        List = []
        while True:
            Byte = self.ReadByte(True)
            if Byte == "e":
                break
            Element = self.ReadElement()
            if Element == None:
                self.ReadByte()
                continue
            List.append(Element)
        self.ReadByte()
        return List
    
    def ReadDictionary(self):
        """Format: d<Dictionary Elements>e
           Element: <Byte Array><Element>"""
        Type = self.ReadByte()
        if Type != "d":
            raise BCode.BCodeError("Element is not a dictionary")
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
        TypeSwitch = dict({
            "i": self.ReadNumber,
            "l": self.ReadList,
            "d": self.ReadDictionary, }, **{
            AnyDigit: self.ReadByteArray
                for AnyDigit in self.DigitsGenerator()
        })
        if not Type in TypeSwitch:
            return None
        return TypeSwitch[Type]()
    
    def ReadByte(self, Quiet=False):
        Byte = self.File.read(1)
        if len(Byte) == 0:
            raise BCode.BCodeError("End of file")
        if Quiet:
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
        try:
            Digits = int(Digits)
        except:
            Digits = 0
        return Digits
    
    def DigitsGenerator(self):
        for x in xrange(10):
            yield str(x)
        yield "-"
