#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: elective.py
# modified: 2019-09-10

__all__ = ["ElectiveClient"]

import random
from .client import BaseClient
from .hook import *
from .const import USER_AGENT, DEFAULT_CLIENT_TIMEOUT, ElectiveLinks


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


def _get_headers_with_referer(kwargs, referer=ElectiveLinks.HelpController):
    headers = kwargs.pop("headers", {})
    headers["Referer"] = referer
    return headers


class ElectiveClient(BaseClient):

    HEADERS = {
        # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        # "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Host": ElectiveLinks.Host,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": USER_AGENT,
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
        r = self._get(
            url=ElectiveLinks.SSOLogin,
            params={
                "rand": str(random.random()),
                "token": token,
            },
            # 必须要随便指定一个 Cookie 否则无法会报 101 status_code
            headers={
                "Cookie": "JSESSIONID=TH9sd1HBgw0k3RTFxMHKmWpPp4bMJ5FnTGn7WmvyH2JmTqNGgxpS!1984960435",
            },
            hooks=_hooks_check_title,
            **kwargs,
        ) # 无 Referer
        return r

    def sso_login_dual_degree(self, sida, sttp, referer, **kwargs):
        assert len(sida) == 32
        assert sttp in ("bzx", "bfx")
        headers = kwargs.pop("headers", {})
        headers["Referer"] = referer # 为之前登录的链接
        r = self._get(
            url=ElectiveLinks.SSOLoginDualDegree,
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
            url=ElectiveLinks.Logout,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_HelpController(self, **kwargs):
        """ 帮助 """
        r = self._get(
            url=ElectiveLinks.HelpController,
            hooks=_hooks_check_title,
            **kwargs,
        ) # 无 Referer
        return r

    def get_PlanController(self, **kwargs):
        """ 选课计划 """
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveLinks.ElectivePlanController,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_WorkController(self, **kwargs):
        """ 预选 """
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveLinks.ElectiveWorkController,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_ShowResults(self, **kwargs):
        """ 选课结果 """
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveLinks.ShowResults,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_SupplyCancel(self, **kwargs):
        """ 补退选 """
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveLinks.SupplyCancel,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_supplement(self, page=1, **kwargs): # 辅双第二页，通过输入数字 2 进行跳转
        assert page > 0
        headers = _get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        r = self._get(
            url=ElectiveLinks.Supplement + "?netui_row=electResultLisGrid%3B0",
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

    def get_SupplyOnly(self, **kwargs):
        """ 补选 """
        headers = _get_headers_with_referer(kwargs)
        r = self._get(
            url=ElectiveLinks.SupplyOnly,
            headers=headers,
            hooks=_hooks_check_title,
            **kwargs,
        )
        return r

    def get_DrawServlet(self, **kwargs):
        """ 获得验证码 """
        headers = _get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        r = self._get(
            url=ElectiveLinks.DrawServlet,
            params={
                "Rand": str(random.random() * 10000),
            },
            headers=headers,
            hooks=_hooks_check_status_code,
            **kwargs,
        )
        return r

    def get_Validate(self, captcha, **kwargs):
        headers = _get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        r = self._post(
            url=ElectiveLinks.Validate,
            data={
                "validCode": captcha,
            },
            headers=headers,
            hooks=_hooks_check_status_code,
            **kwargs,
        )
        return r

    def get_ElectSupplement(self, href, **kwargs):
        headers = _get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        r = self._get(
            url="http://{host}{href}".format(host=ElectiveLinks.Host, href=href),
            headers=headers,
            hooks=_hooks_check_tips,
            **kwargs,
        )
        return r
