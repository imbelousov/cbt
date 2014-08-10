#! /usr/bin/python

"""
Bencode encoding/decoding class.
Usage: bcode.encode(element)
       bcode.decode(string)
Supported element types:
- int
- str
- list
- dict / OrderedDict
Notice: strongly recommend to use OrderedDict instead dict.
"""

import collections
import StringIO
import os.path

__all__ = ["encode", "decode"]

class BCodeStringIO(StringIO.StringIO):
    """Raises error if EOF"""
    def read(self, n=-1):
        r = StringIO.StringIO.read(self, n)
        if len(r) != n:
            self.err()
        return r
    
    def err(self):
        raise ValueError("Invalid bencode string")


def encode(element):
    element_type = type(element)
    switch = {
        int: encode_int,
        str: encode_str,
        list: encode_list,
        dict: encode_dict,
        collections.OrderedDict: encode_dict
    }
    if not element_type in switch:
        return ""
    return switch[element_type](element)

def encode_int(int_val):
    return "i%de" % int_val

def encode_str(str_val):
    return "%d:%s" % (len(str_val), str_val)

def encode_list(list_obj):
    encoded_list = ""
    for element in list_obj:
        encoded_element = encode(element)
        encoded_list = "".join((encoded_list, encoded_element))
    return "l%se" % encoded_list

def encode_dict(dict_obj):
    encoded_dict = ""
    for key, value in dict_obj.iteritems():
        if type(key) != str:
            key = str(key)
        encoded_key = encode_str(key)
        encoded_value = encode(value)
        encoded_dict = "".join((encoded_dict, encoded_key, encoded_value))
    return "d%se" % encoded_dict

def decode(string):
    stream = BCodeStringIO(string)
    element = read_element(stream)
    stream.close()
    return element

def read_element(stream):
    """Automatic type recognizing"""
    byte = stream.read(1)
    stream.seek(-1, 1)
    switch = dict({
        "i": read_int,
        "l": read_list,
        "d": read_dict }, **{
        digit: read_str
            for digit in digits()
    })
    if not byte in switch:
        return None
    return switch[byte](stream)

def read_int(stream):
    """Format: i<digits>e"""
    byte = stream.read(1)
    if byte != "i":
        stream.err()
    string = ""
    int_val = read_number(stream)
    while True:
        byte = stream.read(1)
        if byte == "e":
            break
    return int_val

def read_str(stream):
    """Format: <length (only digits)>:<string>"""
    str_val_len = read_number(stream)
    byte = stream.read(1)
    if byte != ":":
        stream.err()
    str_val = stream.read(str_val_len)
    return str_val

def read_list(stream):
    """Format: l<element 1><element 2>...<element n>e"""
    byte = stream.read(1)
    if byte != "l":
        stream.err()
    list_obj = []
    while True:
        byte = stream.read(1)
        if byte == "e":
            break
        stream.seek(-1, 1)
        element = read_element(stream)
        if element == None:
            stream.read(1)
            continue
        list_obj.append(element)
    return list_obj

def read_dict(stream):
    """Format: d<dict_element 1><dict_element 2>...<dict_element n>e ; dict_element: <str><element>"""
    byte = stream.read(1)
    if byte != "d":
        stream.err()
    dict_obj = collections.OrderedDict()
    while True:
        byte = stream.read(1)
        if byte == "e":
            break
        stream.seek(-1, 1)
        key = read_str(stream)
        value = read_element(stream)
        dict_obj.update({key: value})
    return dict_obj

def read_number(stream):
    """Reads pure digits from stream"""
    string = ""
    while True:
        byte = stream.read(1)
        if not byte in digits():
            break
        string = "".join((string, byte))
    stream.seek(-1, 1)
    if len(string) == 0:
        return 0
    return int(string)

def digits():
    for x in xrange(10):
        yield str(x)
    yield "-"    

"""class BCode():

    def __init__(self):
        self.File = None
    
    def Decode(self, EncodedString):
        \"""Converts bencode to element, generally dictionary\"""
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
        \"""Converts .torrent file contents to element\"""
        IsFileExists = os.path.isfile(FileName)
        if not IsFileExists:
            raise BCodeError("File does not exist")
        if self.File:
            self.File.close()
        try:
            self.File = open(FileName, "rb")
        except:
            raise BCodeError("Access denied")
        Element = self.ReadElement()
        self.File.close()
        self.File = 0
        return Element
    
    def Encode(self, Element):
        \"""Converts element to bencode string\"""
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
        \"""Format: i<Digits>e\"""
        Type = self.ReadByte()
        if Type != "i":
            raise BCodeError("Element is not a number")
        Number = self.ReadDigits()
        while True:
            Byte = self.ReadByte()
            if Byte == "e":
                break
        return Number
    
    def ReadByteArray(self):
        \"""Format: <Array Size>:<Array Bytes>\"""
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
        \"""Format: l<Elements>e\"""
        Type = self.ReadByte()
        if Type != "l":
            raise BCodeError("Element is not a list")
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
        \"""Format: d<Dictionary Elements>e
           Element: <Byte Array><Element>\"""
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
        \"""Automatic type recognizing\"""
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
            raise BCodeError("End of file")
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
"""