#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: elective.py
# modified: 2019-09-10

import random
from urllib.parse import quote
from .client import BaseClient
from .hook import get_hooks, debug_dump_request, debug_print_request, check_status_code, with_etree,\
    check_elective_title, check_elective_tips
from .const import USER_AGENT_LIST, ElectiveURL

_hooks_check_status_code = get_hooks(
    # debug_dump_request,
    debug_print_request,
    check_status_code,
)

_hooks_check_title = get_hooks(
    debug_dump_request,
    debug_print_request,
    check_status_code,
    with_etree,
    check_elective_title,
)

_hooks_check_tips = get_hooks(
    debug_dump_request,
    debug_print_request,
    check_status_code,
    with_etree,
    check_elective_title,
    check_elective_tips,
)

_DUMMY_COOKIES = "JSESSIONID=TH9sd1HBgw0k3RTFxMHKmWpPp4bMJ5FnTGn7WmvyH2JmTqNGgxpS!1984960435"


def _get_headers_with_referer(kwargs, referer=ElectiveURL.HelpController):
    headers = kwargs.pop("headers", {})
    headers["Referer"] = referer
    return headers


class ElectiveClient(BaseClient):

    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Host": ElectiveURL.Host,
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "User-Agent": random.choice(USER_AGENT_LIST),
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
    }

    def __init__(self, id, **kwargs):
        super().__init__(**kwargs)
        self._id = id

    @property
    def id(self):
        return self._id

    @property
    def hasLogined(self):
        return len(self._session.cookies) > 0


    def sso_login(self, token, **kwargs):
        headers = kwargs.pop("headers", {}) # no Referer
        headers["Cookie"] = _DUMMY_COOKIES  # 必须要指定一个 Cookie 否则报 101 status_code
        headers["Sec-Fetch-Site"] = "cross-site"
        r = self._get(
            url=ElectiveURL.SSOLogin,
            params={
                "rand": str(random.random()),
                "token": token,
            },
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def sso_login_dual_degree(self, sida, sttp, referer, **kwargs):
        assert len(sida) == 32
        assert sttp in ("bzx", "bfx")
        headers = kwargs.pop("headers", {}) # no Referer
        headers["Sec-Fetch-Site"] = "cross-site"
        r = self._get(
            url=ElectiveURL.SSOLogin,
            params={
                "sida": sida,
                "sttp": sttp,
            },
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def logout(self, **kwargs):
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveURL.Logout,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_HelpController(self, **kwargs):
        """ 帮助 """
        r = self._get(
            url=ElectiveURL.HelpController,
            hooks=_hooks_check_title,
            **kwargs,
        ) # 无 Referer
        return r

    def get_ShowResults(self, **kwargs):
        """ 选课结果 """
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveURL.ShowResults,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_SupplyCancel(self, **kwargs):
        """ 补退选 """
        headers = _get_headers_with_referer(kwargs)
        headers["Cache-Control"] = "max-age=0"
        r = self._get(
            url=ElectiveURL.SupplyCancel,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_supplement(self, page=1, **kwargs):
        """ 补退选（第二页及以后） """
        assert page > 0
        headers = _get_headers_with_referer(kwargs, ElectiveURL.SupplyCancel)
        headers["Cache-Control"] = "max-age=0"
        r = self._get(
            url=ElectiveURL.Supplement + "?netui_row=%s" % quote("electResultLisGrid;0"),
            params={
                # "netui_row": "electResultLisGrid;0", # leave this field in url for duplicate key 'netui_row'
                "netui_row": "electableListGrid;%s" % ( (page - 1) * 50 ),
                "conflictCourse": "",
            },
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_DrawServlet(self, **kwargs):
        """ 获得验证码 """
        headers = _get_headers_with_referer(kwargs, ElectiveURL.SupplyCancel)
        r = self._get(
            url=ElectiveURL.DrawServlet,
            params={
                "Rand": str(random.random() * 10000),
            },
            headers=headers,
            hooks=_hooks_check_status_code,
            **kwargs,
        )
        return r

    def get_Validate(self, captcha, **kwargs):
        """ 验证用户输入的验证码 """
        headers = _get_headers_with_referer(kwargs, ElectiveURL.SupplyCancel)
        headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        headers["Accept-Encoding"] = "gzip, deflate, br"
        headers["Accept-Language"] = "en-US,en;q=0.9"
        headers["X-Requested-With"] = "XMLHttpRequest"
        r = self._post(
            url=ElectiveURL.Validate,
            data={
                "validCode": captcha,
            },
            headers=headers,
            hooks=_hooks_check_status_code,
            **kwargs,
        )
        return r

    def get_ElectSupplement(self, href, **kwargs):
        """ 补选一门课 """

        if "/supplement/electSupplement.do" not in href:
            raise RuntimeError(
                "If %r is really a 'electSupplement' href, it would certainly contains '/supplement/electSupplement.do'. "
                "If you see this error, that means maybe something terrible will happpen ! Please raise an issue at "
                "https://github.com/zhongxinghong/PKUAutoElective/issues" % href
            )

        headers = _get_headers_with_referer(kwargs, ElectiveURL.SupplyCancel)
        r = self._get(
            url="%s://%s%s" % (ElectiveURL.Scheme, ElectiveURL.Host, href),
            headers=headers,
            hooks=_hooks_check_tips,
            **kwargs,
        )
        return r
