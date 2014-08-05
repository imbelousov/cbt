#!/usr/bin/python

import collections
import os.path
import cStringIO

class Bencode():
    def __init__(self):
        self._File = None
        self._Data = None

    def OpenFromFile(self, FileName):
        """Makes .torrent file ready to read"""
        self._FileName = FileName
        IsFileExists = os.path.isfile(self._FileName)
        if not IsFileExists:
            raise RuntimeError("File does not exist")
        if self._File:
            self.Close()
        self._File = open(self._FileName, "rb")

    def OpenFromString(self, String):
        """Makes string stream from string"""
        if self._File:
            self.Close()
        self._File = cStringIO.StringIO()
        self._File.write(String)
        self._File.seek(0)

    def OpenFromElement(self, Element):
        """Makes any element ready to encode"""
        if self._File:
            self.Close()
        self._Data = Element

    def Decode(self):
        """Converts Bencode to element, generally dictionary"""
        if not self._File:
            raise RuntimeError("Cannot read file")
        self._Data = self._ReadElement()
        return self._Data

    def Close(self):
        if not self._File:
            if self._Data:
                self._Data = None
            return
        self._File.close()
        self._File = None

    def Encode(self, Element=None):
        """Converts element to Bencode string"""
        if Element == None:
            Element = self._Data
        Type = type(Element)
        EncodedString = ""
        if Type in (dict, collections.OrderedDict):
            for Key in Element:
                Value = Element[Key]
                KeyEncoded = self.Encode(Key)
                ValueEncoded = self.Encode(Value)
                EncodedString = "%s%s%s" % (EncodedString, KeyEncoded, ValueEncoded)
            EncodedString = "%s%s%s" % ("d", EncodedString, "e")
        elif Type == list:
            for Item in Element:
                ItemEncoded = self.Encode(Item)
                EncodedString = "%s%s" % (EncodedString, ItemEncoded)
            EncodedString = "%s%s%s" % ("l", EncodedString, "e")
        elif Type == int:
            EncodedString = "%s%s%s" % ("i", str(Element), "e")
        elif Type == str:
            EncodedString = "%s%s:%s" % (EncodedString, len(Element), Element)
        return EncodedString

    def _ReadNumber(self):
        """Format: i<Digits>e"""
        Type = self._ReadByte()
        if Type != "i":
            raise RuntimeError("Element is not a number")
        Number = self._ReadDigits()
        self._ReadByte()
        return Number

    def _ReadByteArray(self):
        """Format: <Array Size>:<Array Bytes>"""
        Type = self._ReadByte(True)
        if not Type in self._DigitsGenerator():
            raise RuntimeError("Element is not a byte array")
        Size = self._ReadDigits()
        self._ReadByte()
        ByteArray = ""
        for x in xrange(Size):
            Byte = self._ReadByte()
            ByteArray += Byte
        return ByteArray

    def _ReadList(self):
        """Format: l<Elements>e"""
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

    def _ReadDictionary(self):
        """Format: d<Dictionary Elements>e
           Element: <Byte Array><Element>"""
        Type = self._ReadByte()
        if Type != "d":
            raise RuntimeError("Element is not a dictionary")
        Dictionary = collections.OrderedDict()
        while True:
            Byte = self._ReadByte(True)
            if Byte == "e":
                break
            Key = self._ReadByteArray()
            Value = self._ReadElement()
            Dictionary[Key] = Value
        self._ReadByte()
        return Dictionary

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
        else:
            raise RuntimeError("Unknown format")

    def _ReadByte(self, quiet=False):
        Byte = self._File.read(1)
        if quiet:
            self._File.seek(-1, 1)
        return Byte

    def _ReadDigits(self):
        Digits = ""
        while True:
            Byte = self._ReadByte()
            if Byte in self._DigitsGenerator():
                Digits += Byte
            else:
                self._File.seek(-1, 1)
                break
        Digits = int(Digits)
        return Digits

    def _DigitsGenerator(self):
        return [str(x) for x in xrange(10)]
