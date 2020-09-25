#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: _internal.py
# modified: 2019-09-08

import os
import gzip

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def absp(*paths):
    return os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), *paths)))

def read_list(file, encoding='utf-8-sig', **kwargs):
    if file.endswith('.gz'):
        fp = gzip.open(file, 'rt', encoding=encoding, **kwargs)
    else:
        fp = open(file, 'r', encoding=encoding, **kwargs)
    try:
        return [ line.rstrip('\n') for line in fp if not line.isspace() ]
    finally:
        fp.close()
