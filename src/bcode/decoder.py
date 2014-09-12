from collections import OrderedDict

__all__ = ["decode"]


def decode(string):
    """Convert bencode string to object."""
    if not isinstance(string, basestring):
        raise TypeError("string required")
    element, _ = _decode_element(string, 0)
    return element


def _decode_element(string, pos):
    """Recognize object type and call appropriate decoder.
    Each decoder takes and returns current position in <string>
    processing.

    """
    type_mark, _ = _read_next(string, pos)
    if type_mark == "i":
        element, pos = _decode_integer(string, pos)
    elif type_mark == "l":
        element, pos = _decode_list(string, pos)
    elif type_mark == "d":
        element, pos = _decode_dict(string, pos)
    elif '0' <= type_mark <= '9' or type_mark == '-':
        element, pos = _decode_bytes(string, pos)
    else:
        raise NotImplementedError("Unsupported element type")
    return element, pos


def _decode_integer(string, pos):
    """Format: i[-]<decimal numbers>e"""
    pos += 1
    result, pos = _read_number(string, pos)
    mark, pos = _read_next(string, pos)
    if mark != 'e':
        raise IOError("Invalid bencode")
    return result, pos


def _decode_bytes(string, pos):
    """Format: <byte array length (decimal numbers)>:<byte array>"""
    length, pos = _read_number(string, pos)
    if length < 0:
        raise IOError("Invalid bencode")
    separator, pos = _read_next(string, pos)
    if separator != ':':
        raise IOError("Invalid bencode")
    result, pos = _read_next(string, pos, length)
    return result, pos


def _decode_list(string, pos):
    """Format: l[<element 1><element 2>...]e"""
    pos += 1
    result = []
    while True:
        mark, _ = _read_next(string, pos)
        if mark == 'e':
            pos += 1
            break
        element, pos = _decode_element(string, pos)
        result.append(element)
    return result, pos


def _decode_dict(string, pos):
    """Format: d[<key 1 (byte array)><element 1><key 2><element 2>...]e"""
    pos += 1
    result = OrderedDict()
    while True:
        mark, _ = _read_next(string, pos)
        if mark == 'e':
            pos += 1
            break
        key, pos = _decode_bytes(string, pos)
        value, pos = _decode_element(string, pos)
        result[key] = value
    return result, pos


def _read_next(string, pos, length=1):
    """Read <length> bytes from the buffer."""
    _string = string[pos:pos+length]
    if len(_string) != length:
        raise IOError("Invalid bencode")
    _pos = pos + len(_string)
    return _string, _pos


def _read_number(string, pos):
    """Read only decimal numbers from the buffer."""
    _pos = pos
    number_bytes = []
    while True:
        byte, _pos = _read_next(string, _pos)
        if '0' <= byte <= '9' or (byte == '-' and _pos == pos + 1):
            number_bytes.append(byte)
        else:
            _pos -= 1
            break
    if not len(number_bytes):
        raise IOError("Invalid bencode")
    number_str = "".join(number_bytes)
    number = int(number_str)
    return number, _pos
