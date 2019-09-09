#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: iaaa.py
# modified: 2019-09-09

__all__ = ["IAAAClient"]

import time
from .client import BaseClient
from .hook import *
from .logger import ConsoleLogger
from .utils import Singleton
from .config import AutoElectiveConfig
from .const import USER_AGENT, IAAALinks, ElectiveLinks
from .exceptions import IAAANotSuccessError


_config = AutoElectiveConfig()
_logger = ConsoleLogger("iaaa")

_hooks_check_iaaa_success = get_hooks(
    debug_print_request,
    check_status_code,
    check_iaaa_success,
)


class IAAAClient(BaseClient, metaclass=Singleton):

    HEADERS = {
        "Host": IAAALinks.Host,
        "Origin": "https://%s" % IAAALinks.Host,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }

    TIMEOUT = _config.iaaaClientTimeout

    def __init__(self):
        super(IAAAClient, self).__init__()
        self._token = None
        self._token_expired_time = None


    @property
    def token(self):
        return self._token

    @property
    def isTokenExpired(self):
        if self._token is None or self._token_expired_time is None:
            return True
        return time.time() > self._token_expired_time

    def clear_token(self):
        self._token = None
        self._token_expired_time = None


    def oauth_login(self, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Referer"] = IAAALinks.OauthHomePage + \
                            "?appID=syllabus" + \
                            "&appName=%E5%AD%A6%E7%94%9F%E9%80%89%E8%AF%BE%E7%B3%BB%E7%BB%9F" + \
                            "&redirectUrl=%s" % ElectiveLinks.SSOLoginRedirect
        r = self._post(
            url=IAAALinks.OauthLogin,
            data={
                "appid": "syllabus",
                "userName": _config.iaaaID,
                "password": _config.iaaaPassword,
                "randCode": "",
                "smsCode": "",
                "otpCode": "",
                "redirUrl": ElectiveLinks.SSOLoginRedirect,
            },
            headers=headers,
            hooks=_hooks_check_iaaa_success,
            **kwargs,
        )
        self._token = r.json()["token"]
        self._token_expired_time = time.time() + _config.iaaaReloginInterval
