#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: _internal.py
# modified: 2019-09-08

__all__ = [

    "mkdir",
    "abspath"

    "userInfo",
]

import os

userInfo = {} # shared the user's custom options


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def abspath(*paths):
    _BASE_DIR = os.path.dirname(__file__)
    return os.path.normpath(os.path.abspath(os.path.join(_BASE_DIR, *paths)))

