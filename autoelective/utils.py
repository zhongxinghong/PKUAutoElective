#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: utils.py
# modified: 2019-09-09

import os
import pickle
import gzip
import hashlib
from requests.compat import json


def b(s):
    if isinstance(s, (str,int,float)):
        return str(s).encode("utf-8")
    elif isinstance(s, bytes):
        return s
    else:
        raise TypeError("unsupport type %s of %r" % (type(s), s))

def u(s):
    if isinstance(s, bytes):
        return s.decode("utf-8")
    elif isinstance(s, (str,int,float)):
        return str(s)
    else:
        raise TypeError("unsupport type %s of %r" % (type(s), s))

def xMD5(data):
    return hashlib.md5(b(data)).hexdigest()

def xSHA1(data):
    return hashlib.sha1(b(data)).hexdigest()

def json_load(file, *args, **kwargs):
    if not os.path.exists(file):
        return None
    with open(file, "r", encoding="utf-8-sig") as fp:
        try:
            return json.load(fp, *args, **kwargs)
        except json.JSONDecodeError:
            return None

def json_dump(obj, file, *args, **kwargs):
    with open(file, "w", encoding="utf-8") as fp:
        json.dump(obj, fp, *args, **kwargs)

def pickle_gzip_dump(obj, file):
    with gzip.open(file, "wb") as fp:
        pickle.dump(obj, fp)

def pickle_gzip_load(file):
    with gzip.open(file, "rb") as fp:
        return pickle.load(fp)


class Singleton(type):
    """
    Singleton Metaclass
    @link https://github.com/jhao104/proxy_pool/blob/428359c8dada998481f038dbdc8d3923e5850c0e/Util/utilClass.py
    """
    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._inst[cls]
