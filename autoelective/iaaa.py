#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: iaaa.py
# modified: 2019-09-10

import random
from urllib.parse import quote
from .client import BaseClient
from .hook import get_hooks, debug_print_request, check_status_code, check_iaaa_success
from .const import USER_AGENT_LIST, IAAAURL, ElectiveURL

_hooks_check_iaaa_success = get_hooks(
    debug_print_request,
    check_status_code,
    check_iaaa_success,
)


class IAAAClient(BaseClient):

    default_headers = {
        "Host": IAAAURL.Host,
        "Origin": "https://%s" % IAAAURL.Host,
        "User-Agent": random.choice(USER_AGENT_LIST),
        "X-Requested-With": "XMLHttpRequest",
    }

    def oauth_login(self, username, password, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Referer"] = "%s?appID=syllabus&appName=%s&redirectUrl=%s" % (
            IAAAURL.OauthHomePage, quote("学生选课系统"), ElectiveURL.SSOLoginRedirect,
        )
        r = self._post(
            url=IAAAURL.OauthLogin,
            data={
                "appid": "syllabus",
                "userName": username,
                "password": password,
                "randCode": "",
                "smsCode": "",
                "otpCode": "",
                "redirUrl": ElectiveURL.SSOLoginRedirect,
            },
            headers=headers,
            hooks=_hooks_check_iaaa_success,
            **kwargs,
        )
        return r
