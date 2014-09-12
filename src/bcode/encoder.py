__all__ = ["encode"]


def encode(element):
    """Convert object to bencode string."""
    buf = []
    _encode_element(element, buf)
    return "".join(buf)


def _encode_element(element, buf):
    """Call appropriate encoder for type of the element.
    Each encoder appends encoded data to <buf>.

    """
    if isinstance(element, int):
        _encode_integer(element, buf)
    elif isinstance(element, str):
        _encode_bytes(element, buf)
    elif isinstance(element, list):
        _encode_list(element, buf)
    elif isinstance(element, dict):
        _encode_dict(element, buf)
    else:
        raise NotImplementedError("Unsupported element type")


def _encode_integer(element, buf):
    """Format: i[-]<decimal numbers>e"""
    buf.append("i")
    buf.append(str(element))
    buf.append("e")


def _encode_bytes(element, buf):
    """Format: <byte array length (decimal numbers)>:<byte array>"""
    buf.append(str(len(element)))
    buf.append(":")
    buf.append(element)


def _encode_list(element, buf):
    """Format: l[<element 1><element 2>...]e"""
    buf.append("l")
    for item in element:
        _encode_element(item, buf)
    buf.append("e")


def _encode_dict(element, buf):
    """Format: d[<key 1 (byte array)><element 1><key 2><element 2>...]e"""
    buf.append("d")
    for key, value in element.iteritems():
        if not isinstance(key, str):
            raise ValueError("Key must be a string")
        _encode_bytes(key, buf)
        _encode_element(value, buf)
    buf.append("e")
