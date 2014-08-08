#!/usr/bin/python

def CharToBytes(Char):
    return chr(Char)

def IntToBytes(Int):
    Bytes = ""
    for i in xrange(4):
        Digit = Int % 0x100
        Int /= 0x100
        Bytes = chr(Digit) + Bytes
    return Bytes