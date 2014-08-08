#!/usr/bin/python

"""
Gets peer id for current session
"""

import os
import hashlib
import time

PeerId = None

def GetPeerId():
    global PeerId
    if PeerId:
        return PeerId
    Pid = os.getpid()
    Timestamp = time.time()
    UniqueString = "%s_%s" % (Pid, Timestamp)
    PeerId = hashlib.sha1(UniqueString).digest()
    return PeerId