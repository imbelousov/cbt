#! /usr/bin/python

__all__ = ["uint_chr, uint_ord"]

def uint_chr(uint_val, size=4):
    bytes = []
    for i in xrange(size):
        bytes.insert(0, uint_val % 0x100)
        uint_val /= 0x100
    g = [chr(byte) for byte in bytes]
    return "".join(g)

def uint_ord(bytes):
    uint_val = 0
    for byte in bytes:
        uint_val *= 0x100
        uint_val += ord(byte)
    return uint_val
