#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: rule.py
# modified: 2020-02-20

class Mutex(object):

    __slots__ = ["_cids",]

    def __init__(self, cids):
        self._cids = cids

    @property
    def cids(self):
        return self._cids


class Delay(object):

    __slots__ = ["_cid","_threshold"]

    def __init__(self, cid, threshold):
        assert threshold > 0
        self._cid = cid
        self._threshold = threshold

    @property
    def cid(self):
        return self._cid

    @property
    def threshold(self):
        return self._threshold

