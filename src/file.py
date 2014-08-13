#! /usr/bin/python

import os

__all__ = ["File"]

class File(object):
    def __init__(self, name, path, length):
        if path[-1] == os.sep:
            path = path[:-1]
        if type(name) is str:
            n = os.sep.join((path, name))
            self.name = os.path.abspath(n)
        elif type(name) is list:
            name = name[:]
            name.insert(0, path)
            n = os.sep.join(name)
            self.name = n
        else:
            raise TypeError("str or list expected")
        self.length = length

    def create(self):
        path = os.sep.join(self.name.split(os.sep)[:-1])
        if not os.path.isdir(path):
            os.makedirs(path)
        if os.path.isfile(self.name):
            if os.path.getsize(self.name) == self.length:
                return
        with open(self.name, "wb") as f:
            f.seek(self.length - 1, 1)
            f.write("\0")
