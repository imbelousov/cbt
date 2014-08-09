#! /usr/bin/python
# -*- coding: utf-8 -*-

class CbtError():
    def __init__(self, ErrStr=""):
        self.ErrStr = ErrStr
    
    def __str__(self):
        return self.ErrStr