#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: client.py

import os
import requests
from requests.cookies import RequestsCookieJar
from .util import json_load, json_dump
from .const import Cache_Dir
from .exceptions import ABCNotImplementedError

__all__ = ["ClientMixin",]


class ClientMixin(object):

    Timeout = 10
    Proxies = {}
    Cookies_File = None
    Headers = {}

    def __init__(self, *args, **kwargs):
        if self.__class__ is __class__: # 不可实例化
            raise ABCNotImplementedError
        self.__cookies_filename = os.path.abspath(os.path.join(
                                    Cache_Dir, "%s.cookies.json" % self.__class__.__name__))
        self._session = requests.session()
        self._session.headers.update(self.__class__.Headers)
        self._session.cookies = self._load_cookies()
        self._session.proxies = self.__class__.Proxies

    def _request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.__class__.Timeout)
        return self._session.request(method, url, **kwargs)

    def _get(self, url, params=None, **kwargs):
        return self._request('GET', url,  params=params, **kwargs)

    def _post(self, url, data=None, json=None, **kwargs):
        return self._request('POST', url, data=data, json=json, **kwargs)

    def _save_cookies(self):
        json_dump(self._session.cookies.get_dict(), self.__cookies_filename)

    def _load_cookies(self):
        cookies = json_load(self.__cookies_filename)
        if cookies is None:
            return RequestsCookieJar()
        else:
            jar = RequestsCookieJar()
            for k, v in cookies.items():
                jar.set(k, v)
            return jar

    def clean_cookies(self):
        self._session.cookies.clear()
