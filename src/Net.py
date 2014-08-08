#!/usr/bin/python

from Errors import CbtError

class NetError(CbtError):
    def __init__(self, Error):
        print Error

def CharToBytes(Char):
    if Char > 0xFF or Char < 0:
        NetError("Char -> Bytes packing error")
    return chr(Char)

def IntToBytes(Int):
    if Int > 0xFFFFFFFF or Int < 0:
        NetError("Int -> Bytes packing error")
    Bytes = ""
    for i in xrange(4):
        Digit = Int % 0x100
        Int /= 0x100
        Bytes = chr(Digit) + Bytes
    return Bytes

def BytesToChar(Bytes):
    if len(Bytes) != 1:
        NetError("Bytes -> Char unpacking error")
    return ord(Bytes)

def BytesToInt(Bytes):
    if len(Bytes) != 4:
        NetError("Bytes -> Int unpacking error")
    Int = 0
    for Byte in Bytes:
        Int *= 0x100
        Int += ord(Byte)