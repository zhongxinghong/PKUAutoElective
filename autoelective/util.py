#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: util.py

import os
import csv
from copy import deepcopy
import hashlib
from functools import wraps
from collections import OrderedDict
from ._compat import json, JSONDecodeError
from .exceptions import NoInstanceError, ImmutableTypeError, ReadonlyPropertyError


__Util_Funcs__     = ["mkdir","json_load","json_dump","read_csv","to_bytes","to_utf8","MD5","SHA1",]
__Util_Class__     = ["ImmutableAttrsMixin",]
__Util_Decorator__ = ["singleton","noinstance","ReadonlyProperty",]
__Util_MetaClass__ = ["Singleton","NoInstance",]

__all__ = __Util_Funcs__ + __Util_Class__ + __Util_Decorator__ + __Util_MetaClass__


def to_bytes(s):
    if isinstance(s, (str,int,float)):
        return str(s).encode("utf-8")
    elif isinstance(s, bytes):
        return s
    else:
        raise TypeError

def to_utf8(s):
    if isinstance(s, bytes):
        return s.decode("utf-8")
    elif isinstance(s, (str,int,float)):
        return str(s)
    else:
        raise TypeError

def MD5(data):
    return hashlib.md5(to_bytes(data)).hexdigest()

def SHA1(data):
    return hashlib.sha1(to_bytes(data)).hexdigest()


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def json_load(file, *args, **kwargs):
    if not file:
        return None
    elif not os.path.exists(file):
        return None
    else:
        with open(file, "r", encoding="utf-8-sig") as fp:
            try:
                return json.load(fp, *args, **kwargs)
            except JSONDecodeError:
                return None

def json_dump(obj, file, *args, **kwargs):
    with open(file, "w", encoding="utf-8") as fp:
        json.dump(obj, fp, *args, **kwargs)

def read_csv(file, encoding="utf-8-sig"):
    with open(file, "r", encoding=encoding, newline="") as fp:
        reader = csv.DictReader(fp)
        return [_ for _ in reader]


def noinstance(cls):
    """ 被修饰类不能被继承！ """
    @wraps(cls)
    def wrapper(*args, **kwargs):
        raise NoInstanceError("class %s cannot be instantiated" % cls.__name__)
    return wrapper

def singleton(cls):
    """ 被修饰类不能被继承！ """
    _inst = {}
    @wraps(cls)
    def get_inst(*args, **kwargs):
        if cls not in _inst:
            _inst[_cls] = _cls(*args, **kwargs)
        return _inst[cls]
    return get_inst


class Singleton(type):
    """
    Singleton Metaclass
    @link https://github.com/jhao104/proxy_pool/blob/428359c8dada998481f038dbdc8d3923e5850c0e/Util/utilClass.py
    """
    _inst = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._inst:
            cls._inst[cls] = super(Singleton, cls).__call__(*args)
        return cls._inst[cls]

class NoInstance(type):

    def __call__(cls, *args, **kwargs):
        raise NoInstanceError("class %s cannot be instantiated" % cls.__name__)


def _is_readonly(obj, key):
    raise ReadonlyPropertyError("'%s.%s' property is read-only" % (obj.__class__.__name__, key))


class ReadonlyProperty(property):
    """ 只读属性 """
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        super().__init__(fget, None, None, doc) # 直接丢弃 fset, fdel

    def __set__(self, obj, value):
        _is_readonly(obj, self.fget.__name__)

    def __delete__(self, obj):
        _is_readonly(obj, self.fget.__name__)


def _is_immutable(self):
    raise ImmutableTypeError('%r objects are immutable' % self.__class__.__name__)


class ImmutableDictMixin(object):
    """
    @link https://github.com/pallets/werkzeug/blob/master/werkzeug/datastructures.py
    Makes a :class:`dict` immutable.
    .. versionadded:: 0.5
    :private:
    """
    _hash_cache = None

    @classmethod
    def fromkeys(cls, keys, value=None):
        instance = super(cls, cls).__new__(cls)
        instance.__init__(zip(keys, repeat(value)))
        return instance

    def __reduce_ex__(self, protocol):
        return type(self), (dict(self),)

    def _iter_hashitems(self):
        return iteritems(self)

    def __hash__(self):
        if self._hash_cache is not None:
            return self._hash_cache
        rv = self._hash_cache = hash(frozenset(self._iter_hashitems()))
        return rv

    def setdefault(self, key, default=None):
        _is_immutable(self)

    def update(self, *args, **kwargs):
        _is_immutable(self)

    def pop(self, key, default=None):
        _is_immutable(self)

    def popitem(self):
        _is_immutable(self)

    def __setitem__(self, key, value):
        _is_immutable(self)

    def __delitem__(self, key):
        _is_immutable(self)

    def clear(self):
        _is_immutable(self)


class ImmutableDict(ImmutableDictMixin, dict):
    """
    @link https://github.com/pallets/werkzeug/blob/master/werkzeug/datastructures.py
    An immutable :class:`dict`.
    .. versionadded:: 0.5
    """
    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            dict.__repr__(self),
        )

    def copy(self):
        """Return a shallow mutable copy of this object.  Keep in mind that
        the standard library's :func:`copy` function is a no-op for this class
        like for any other python immutable type (eg: :class:`tuple`).
        """
        return dict(self)

    def __copy__(self):
        return self


class ImmutableAttrsMixin(object):
    """
    very ugly !!!
    一种不可变对象的实现
    只允许创建时赋值，创建后不能再修改：
        - 不能通过 __setattr__/__delattr__ 实现修改
        - 不能通过 __dict__.__setitem__/__delitem__ 实现修改
    关于复制：
        - 调用 copy.copy     返回本身
        - 调用 copy.deepcopy 返回新对象
    """
    __cache_init = {}

    def __init__(self, *args, **kwargs):
        ### 重置 __init__ ###
        #print("ImmutableAttrsMixin.__init__")
        self.__class__.__init__ = __class__.__cache_init[self.__class__.__name__]

    def __new__(cls, *args, **kwargs):
        #print("ImmutableAttrsMixin.__new__ Start")
        ### 暂时允许修改 ###
        cls.__setattr__ = object.__setattr__
        cls.__delattr__ = object.__delattr__
        ### 初始化对象 ###
        obj = object.__new__(cls)
        cls.__init__(obj, *args, **kwargs)
        ### 禁止通过 __dict__ 修改对象 ###
        obj.__dict__ = ImmutableDict(obj.__dict__)
        ### 重新设置为不允许修改，并取消 __init__ 函数 ###
        cls.__setattr__ = __class__.__setattr__
        cls.__delattr__ = __class__.__delattr__
        ### 暂时取消 __init__ 函数，避免自动 __init__ 时报错 ###
        __class__.__cache_init[cls.__name__] = cls.__init__
        cls.__init__ = __class__.__init__
        #print("ImmutableAttrsMixin.__new__ End")
        return obj

    def __setattr__(self, key, value):
        #print("ImmutableAttrsMixin.__setitem__")
        _is_immutable(self)

    def __delattr__(self, key):
        #print("ImmutableAttrsMixin.__delitem__")
        _is_immutable(self)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo=None):
        """
        @link https://github.com/pallets/werkzeug/blob/master/werkzeug/datastructures.py  --> MultiDict
        """
        return self.__class__(**deepcopy(self.__dict__, memo=memo))
