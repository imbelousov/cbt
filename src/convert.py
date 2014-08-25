__all__ = ["uint_chr, uint_ord"]


def uint_chr(uint_val, size=4):
    """Convert unsigned integer to bytes array
    with network byte order.

    """
    bytes = []
    for _ in xrange(size):
        bytes.insert(0, chr(uint_val % 0x100))
        uint_val /= 0x100
    return "".join(bytes)


def uint_ord(bytes):
    """Convert network-ordered byte array
    to unsigned integer.

    """
    uint_val = 0
    for byte in bytes:
        uint_val *= 0x100
        uint_val += ord(byte)
    return uint_val
