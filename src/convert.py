#! /usr/bin/python

__all__ = ["uint_chr, uint_ord"]


def uint_chr(uint_val, size=4):
    """Convert unsigned integer to bytes array
    with network byte order.

    """
    bytes = []
    for _ in xrange(size):
        bytes.insert(0, uint_val % 0x100)
        uint_val /= 0x100
    bytes_list = [chr(byte) for byte in bytes]
    return "".join(bytes_list)


def uint_ord(bytes):
    """Convert network-ordered byte array
    to unsigned integer.

    """
    uint_val = 0
    for byte in bytes:
        uint_val *= 0x100
        uint_val += ord(byte)
    return uint_val
