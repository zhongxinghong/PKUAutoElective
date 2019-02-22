#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: iaaa.py

import os
import time
from ._compat import json
from .client import ClientMixin
from .hook import get_hooks, merge_hooks, check_status_code, check_iaaa_success
from .logger import ConsoleLogger
from .util import json_load, json_dump, Singleton, ReadonlyProperty
from .config import generalCfg
from .const import Cache_Dir, User_Agent, IAAALinks, ElectiveLinks
from .exceptions import IAAANotSuccessError

__all__ = ["IAAAClient",]


class IAAAClient(ClientMixin, metaclass=Singleton):

    Headers = {
        "Host": IAAALinks.Host,
        "Origin": "https://%s" % IAAALinks.Host,
        "User-Agent": User_Agent,
        "X-Requested-With": "XMLHttpRequest",
    }
    __logger = ConsoleLogger("iaaa")

    def __init__(self):
        super(IAAAClient, self).__init__()
        self.__token_filename = os.path.abspath(os.path.join(
                    Cache_Dir, "%s.token.json" % __class__.__name__))
        self.__token = self._load_token()
        self.__hooks_check_status_code = get_hooks(check_status_code)
        self.__hooks_check_iaaa_success = merge_hooks(self.__hooks_check_status_code, check_iaaa_success)

    @ReadonlyProperty
    def token(self):
        return self.__token

    def oauth_login(self, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Referer"] = IAAALinks.OauthHomePage + \
                            "?appID=syllabus" + \
                            "&appName=%E5%AD%A6%E7%94%9F%E9%80%89%E8%AF%BE%E7%B3%BB%E7%BB%9F" + \
                            "&redirectUrl=%s" % ElectiveLinks.SSOLoginRedirect
        resp = self._post(IAAALinks.OauthLogin,
            data = {
                "appid": "syllabus",
                "userName": generalCfg.get("user","StudentID"),
                "password": generalCfg.get("user","Password"),
                "randCode": "",
                "smsCode": "",
                "otpCode": "",
                "redirUrl": ElectiveLinks.SSOLoginRedirect,
            },
            headers = headers,
            hooks = self.__hooks_check_iaaa_success,
            **kwargs
            )
        self.__token = _token = resp.json()["token"]
        self._save_token(_token)
        self._save_cookies()

    def _load_token(self):
        res = json_load(self.__token_filename)
        if res:
            _token = res.get("token")
            if _token and len(_token) == 32: # 校验 token 合理性
                return _token

    def _save_token(self, token):
        self.__logger.info("token: %s" % token)
        json_dump({
                "token": token,
                "timestamp": int(time.time())
            }, self.__token_filename)