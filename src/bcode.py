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
