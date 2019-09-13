#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: iaaa.py
# modified: 2019-09-10

__all__ = ["IAAAClient"]

from .client import BaseClient
from .hook import *
from .const import USER_AGENT, IAAALinks, ElectiveLinks


_hooks_check_iaaa_success = get_hooks(
    debug_print_request,
    check_status_code,
    check_iaaa_success,
)


class IAAAClient(BaseClient):

    HEADERS = {
        "Host": IAAALinks.Host,
        "Origin": "https://%s" % IAAALinks.Host,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }

    def oauth_login(self, username, password, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Referer"] = IAAALinks.OauthHomePage + \
                            "?appID=syllabus" + \
                            "&appName=%E5%AD%A6%E7%94%9F%E9%80%89%E8%AF%BE%E7%B3%BB%E7%BB%9F" + \
                            "&redirectUrl=%s" % ElectiveLinks.SSOLoginRedirect
        r = self._post(
            url=IAAALinks.OauthLogin,
            data={
                "appid": "syllabus",
                "userName": username,
                "password": password,
                "randCode": "",
                "smsCode": "",
                "otpCode": "",
                "redirUrl": ElectiveLinks.SSOLoginRedirect,
            },
            headers=headers,
            hooks=_hooks_check_iaaa_success,
            **kwargs,
        )
        return r
