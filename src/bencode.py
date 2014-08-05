#!/usr/bin/python

import os.path

class Bencode():
    def __init__(self):
        self._File = None

    def Open(self, FileName):
        self._FileName = FileName
        IsFileExists = os.path.isfile(self._FileName)
        if not IsFileExists:
            return False
        self._File = open(self._FileName, "rb")
        return True

    def Read(self):
        """Converts Bencode file contents to element, generally dictionary"""
        if not self._File:
            return None
        self._Data = self._ReadElement()
        return self._Data

    def Close(self):
        if not self._File:
            return
        self._File.close()

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
        Dictionary = {}
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
        else
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
