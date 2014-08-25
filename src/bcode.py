"""
Bencode encoding/decoding module.

Functions:

    bcode.encode(element):
        Convert element to bencode string.

    bcode.decode(string):
        Convert bencode string to element.

Supported element types:
    int
    str
    list
    tuple
    dict
    OrderedDict

"""

import collections
import StringIO

__all__ = ["encode", "decode"]

ordered_dict = collections.OrderedDict


def encode(element):
    """Convert element into bencode bytes.
    Returns a string.
    element may be integer, string, list, tuple,
    dictionary or ordered dictionary

    """
    return _encode_element(element)


def decode(string):
    """Convert bencode bytes into element.
    Returns: string, integer, list, ordered_dict or None

    """
    stream = _make_stream(string)
    return _read_element(stream)


class BCodeStream(StringIO.StringIO):
    """It is necessary to raise an error if cursor has reached EOF
    and stream is going to read next bytes.
    It means that bencoded string is invalid.

    """

    def read(self, n=-1):
        """Raise error if EOF."""
        r = StringIO.StringIO.read(self, n)
        if len(r) != n:
            self.err()
        return r

    def err(self):
        raise IOError("Invalid bencode string")


def _encode_element(element):
    """Convert element into bencode bytes."""
    element_type = type(element)
    switch = {
        int: _encode_int,
        str: _encode_str,
        list: _encode_list,
        dict: _encode_dict,
        ordered_dict: _encode_dict
    }
    assert element_type in switch
    encoder = switch[element_type]
    return encoder(element)


def _encode_int(int_val):
    """Convert integer into bencode bytes."""
    assert type(int_val) is int
    return "i%de" % int_val


def _encode_str(str_val):
    """Convert string into bencode bytes."""
    assert type(str_val) is str
    return "%d:%s" % (len(str_val), str_val)


def _encode_list(list_obj):
    """Convert list into bencode bytes."""
    assert type(list_obj) in (list, tuple)
    elements = ["l"]
    for element in list_obj:
        encoded_element = _encode_element(element)
        elements.append(encoded_element)
    elements.append("e")
    encoded_list = "".join(elements)
    return encoded_list


def _encode_dict(dict_obj):
    """Convert dictionary into bencode bytes."""
    assert type(dict_obj) in (dict, ordered_dict)
    elements = ["d"]
    for key, value in dict_obj.iteritems():
        if type(key) != str:
            key = str(key)
        encoded_key = _encode_str(key)
        elements.append(encoded_key)
        encoded_value = _encode_element(value)
        elements.append(encoded_value)
    elements.append("e")
    encoded_dict = "".join(elements)
    return encoded_dict


def _make_stream(string):
    """Make string stream and initialize its buffer with bencode string."""
    string = str(string)
    return BCodeStream(string)


def _read_element(stream):
    """Recognize element type ; call appropriate handler ; return its result."""
    try:
        byte = stream.read(1)
    except IOError:
        byte = None
    stream.seek(-1, 1)
    switch = dict({
                      "i": _read_int,
                      "l": _read_list,
                      "d": _read_dict}, **{
        digit: _read_str
        for digit in _digits()
    })
    if byte not in switch:
        return None
    reader = switch[byte]
    return reader(stream)


def _read_int(stream):
    """Read whole bencode string from the stream ; convert it to integer.

    Format: i<digits>e

    """
    byte = stream.read(1)
    if byte != "i":
        stream.err()
    string = ""
    int_val = _read_number(stream)
    while True:
        byte = stream.read(1)
        if byte == "e":
            break
    return int_val


def _read_str(stream):
    """Read whole bencode string from the stream ; convert it to ordinary string.

    Format: <length (only digits)>:<string>

    """
    str_val_len = _read_number(stream)
    byte = stream.read(1)
    if byte != ":":
        stream.err()
    str_val = stream.read(str_val_len)
    return str_val


def _read_list(stream):
    """Read whole bencode string from the stream ; convert it to list.

    Format: l<element 1><element 2>...<element n>e

    """
    byte = stream.read(1)
    if byte != "l":
        stream.err()
    list_obj = []
    while True:
        byte = stream.read(1)
        if byte == "e":
            break
        stream.seek(-1, 1)
        element = _read_element(stream)
        if element is None:
            stream.read(1)
            continue
        list_obj.append(element)
    return list_obj


def _read_dict(stream):
    """Read whole bencode string from the stream ; convert it to dictionary.

    Format: d<dict_element 1><dict_element 2>...<dict_element n>e ;
    dict_element: <str><element>

    """
    byte = stream.read(1)
    if byte != "d":
        stream.err()
    dict_obj = ordered_dict()
    while True:
        byte = stream.read(1)
        if byte == "e":
            break
        stream.seek(-1, 1)
        key = _read_str(stream)
        value = _read_element(stream)
        dict_obj.update({key: value})
    return dict_obj


def _read_number(stream):
    """Read digits only from the stream ; return result as integer."""
    string = ""
    while True:
        byte = stream.read(1)
        if byte not in _digits():
            break
        string = "".join((string, byte))
    stream.seek(-1, 1)
    if len(string) == 0:
        return 0
    return int(string)


def _digits():
    """Generates composite elements of a number."""
    for x in xrange(10):
        yield str(x)
    yield "-"
