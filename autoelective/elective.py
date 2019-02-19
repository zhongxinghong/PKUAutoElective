#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: elective.py

import random
from .client import ClientMixin
from .hook import get_hooks, merge_hooks, with_etree,\
    check_status_code, check_elective_title, check_elective_tips#, print_request_info
from .logger import ConsoleLogger
from .util import Singleton
from .const import User_Agent, ElectiveLinks

__all__ = ["ElectiveClient",]


class ElectiveClient(ClientMixin, metaclass=Singleton):

    Headers = {
        "Host": ElectiveLinks.Host,
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": User_Agent,
    }
    Timeout = 30 # elective 拥挤时可能会出现网络堵塞
    __logger = ConsoleLogger("elective")

    def __init__(self):
        super(ElectiveClient, self).__init__()
        self.__hooks_check_status_code = get_hooks(check_status_code)
        self.__hooks_check_title = merge_hooks(self.__hooks_check_status_code, with_etree, check_elective_title)
        self.__hooks_check_tips = merge_hooks(self.__hooks_check_title, check_elective_tips)

    @staticmethod
    def __get_headers_with_referer(kwargs, referer=ElectiveLinks.HelpController):
        headers = kwargs.pop("headers", {})
        headers["Referer"] = referer
        return headers

    def sso_login(self, token, **kwargs):
        resp = self._get(ElectiveLinks.SSOLogin,
            params = {
                "rand": str(random.random()),
                "token": token,
            },
            hooks = self.__hooks_check_title,
            **kwargs
            ) # 无 Referer
        self._save_cookies()
        return resp

    def logout(self, **kwargs):
        headers = self.__get_headers_with_referer(kwargs)
        resp = self._get(ElectiveLinks.Logout,
            headers = headers,
            hooks = self.__hooks_check_title,
            **kwargs
            )
        self._save_cookies()
        return resp

    def get_HelpController(self, **kwargs):
        """ 帮助 """
        resp = self._get(ElectiveLinks.HelpController,
            hooks = self.__hooks_check_title,
            **kwargs
            ) # 无 Referer
        self._save_cookies()
        return resp

    def get_PlanController(self, **kwargs):
        """ 选课计划 """
        headers = self.__get_headers_with_referer(kwargs)
        resp = self._get(ElectiveLinks.ElectivePlanController,
            headers = headers,
            hooks = self.__hooks_check_title,
            **kwargs
            )
        self._save_cookies()
        return resp

    def get_WorkController(self, **kwargs):
        """ 预选 """
        headers = self.__get_headers_with_referer(kwargs)
        resp = self._get(ElectiveLinks.ElectiveWorkController,
            headers = headers,
            hooks = self.__hooks_check_title,
            **kwargs
            )
        self._save_cookies()
        return resp

    def get_ShowResults(self, **kwargs):
        """ 选课结果 """
        headers = self.__get_headers_with_referer(kwargs)
        resp = self._get(ElectiveLinks.ShowResults,
            headers = headers,
            hooks = self.__hooks_check_title,
            **kwargs
            )
        self._save_cookies()
        return resp

    def get_SupplyCancel(self, **kwargs):
        """ 补退选 """
        headers = self.__get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel) # 此 Referer 相当于刷新页面
        resp = self._get(ElectiveLinks.SupplyCancel,
            headers = headers,
            hooks = self.__hooks_check_title,
            **kwargs
            )
        self._save_cookies()
        return resp

    def get_SupplyOnly(self, **kwargs):
        """ 补选 """
        headers = self.__get_headers_with_referer(kwargs)
        resp = self._get(ElectiveLinks.SupplyOnly,
            headers = headers,
            hooks = self.__hooks_check_title,
            **kwargs
            )
        self._save_cookies()
        return resp

    def get_DrawServlet(self, **kwargs):
        """ 获得验证码 """
        headers = self.__get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        resp = self._get(ElectiveLinks.DrawServlet,
            params = {
                "Rand": str(random.random() * 10000),
            },
            headers = headers,
            hooks = self.__hooks_check_status_code,
            **kwargs
            )
        #self._save_cookies()
        return resp

    def get_Validate(self, captcha, **kwargs):
        headers = self.__get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        resp = self._post(ElectiveLinks.Validate,
            data = {
                "validCode": captcha,
            },
            headers = headers,
            hooks = self.__hooks_check_status_code,
            **kwargs
            )
        #self._save_cookies()
        return resp

    def get_ElectSupplement(self, href, **kwargs):
        headers = self.__get_headers_with_referer(kwargs, ElectiveLinks.SupplyCancel)
        resp = self._get("http://{host}{href}".format(host=ElectiveLinks.Host, href=href),
            headers = headers,
            hooks = self.__hooks_check_tips,
            **kwargs
            )
        self._save_cookies()
        return resp
