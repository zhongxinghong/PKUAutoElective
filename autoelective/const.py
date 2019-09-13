#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: const.py
# modified: 2019-09-11

__all__ = [

    "SIGNAL_KILL_ALL_PROCESSES",
    "SIGNAL_KILL_ALL_THREADS",

    "BASE_DIR",
    "MODEL_DIR",
    "CACHE_DIR",
    "LOG_DIR",
    "ERROR_LOG_DIR",
    "CAPTCHA_CACHE_DIR",
    "REQUEST_LOG_DIR",

    "DEFAULT_COURSE_UTF8_CSV",
    "DEFAULT_COURSE_GBK_CSV",
    "DEFAULT_CONFIG_INI",

    "USER_AGENT",
    "DEFAULT_CLIENT_TIMEOUT",

    "IAAALinks",
    "ElectiveLinks",

    ]

import random
from ._internal import mkdir, abspath


SIGNAL_KILL_ALL_PROCESSES = 1
SIGNAL_KILL_ALL_THREADS = 2


BASE_DIR                = abspath("./")
MODEL_DIR               = abspath("./captcha/model/")
CACHE_DIR               = abspath("../cache/")
CAPTCHA_CACHE_DIR       = abspath("../cache/captcha/")
LOG_DIR                 = abspath("../log/")
ERROR_LOG_DIR           = abspath("../log/error")
REQUEST_LOG_DIR         = abspath("../log/request/")

DEFAULT_COURSE_UTF8_CSV = abspath("../course.utf-8.csv")
DEFAULT_COURSE_GBK_CSV  = abspath("../course.gbk.csv")
DEFAULT_CONFIG_INI      = abspath("../config.ini")


mkdir(CACHE_DIR)
mkdir(CAPTCHA_CACHE_DIR)
mkdir(LOG_DIR)
mkdir(ERROR_LOG_DIR)
mkdir(REQUEST_LOG_DIR)


# 警惕直接复制的 User-Agent 中可能存在的省略号（通常源自 Firefox 开发者工具），它可能会引发如下错误：
#   File "/usr/lib/python3.6/http/client.py", line 1212, in putheader
#     values[i] = one_value.encode('latin-1')
# UnicodeEncodeError: 'latin-1' codec can't encode character '\u2026' in position 30: ordinal not in range(256)
USER_AGENT = random.choice([
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 OPR/58.0.3135.65",
    "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:62.0) Gecko/20100101 Firefox/62.0",
])
# USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/75.0.3770.90 Chrome/75.0.3770.90 Safari/537.36"

DEFAULT_CLIENT_TIMEOUT = 10


class IAAALinks(object):
    """
        Host
        OauthHomePage
        OauthLogin
    """
    _BASE_URL    = "https://iaaa.pku.edu.cn/iaaa"

    Host          = "iaaa.pku.edu.cn"
    OauthHomePage = _BASE_URL + "/oauth.jsp"
    OauthLogin    = _BASE_URL + "/oauthlogin.do"


class ElectiveLinks(object):
    """
        Host
        SSOLoginRedirect        重定向链接
        SSOLogin                sso登录
        SSOLoginDualDegree      sso登录（双学位）
        Logout                  登出
        HelpController          选课帮助页
        ElectivePlanController  选课计划页
        ElectiveWorkController  选课页
        ShowResults             选课结果页
        SupplyCancel            补退选页
        CourseQueryController   课程查询页
        GetCurriculmByForm      发送查询表单
        addToPlan               添加课程到选课计划
        DeleElecPlanCurriclum   删除选课计划（补退选阶段）
        validate                补退选验证码校验接口
    """
    _BASE_URL             = "http://elective.pku.edu.cn/elective2008"
    _CONTROLLER_BASE_URL  = _BASE_URL + "/edu/pku/stu/elective/controller"

    Host                   = "elective.pku.edu.cn"
    SSOLoginRedirect       = "http://elective.pku.edu.cn:80/elective2008/agent4Iaaa.jsp/../ssoLogin.do"
    SSOLogin               = _BASE_URL + "/ssoLogin.do"
    SSOLoginDualDegree     = "http://elective.pku.edu.cn:80/elective2008/scnStAthVef.jsp/../ssoLogin.do"
    Logout                 = _BASE_URL + "/logout.do"
    HelpController         = _CONTROLLER_BASE_URL + "/help/HelpController.jpf"
    ElectivePlanController = _CONTROLLER_BASE_URL + "/electivePlan/ElectivePlanController.jpf"
    ElectiveWorkController = _CONTROLLER_BASE_URL + "/electiveWork/ElectiveWorkController.jpf"
    ShowResults            = _CONTROLLER_BASE_URL + "/electiveWork/showResults.do"
    SupplyCancel           = _CONTROLLER_BASE_URL + "/supplement/SupplyCancel.do"
    Supplement             = _CONTROLLER_BASE_URL + "/supplement/supplement.jsp"
    SupplyOnly             = _CONTROLLER_BASE_URL + "/supplement/SupplyOnly.do"
    # CourseQueryController  = _CONTROLLER_BASE_URL + "/courseQuery/CourseQueryController.jpf"
    # GetCurriculmByForm     = _CONTROLLER_BASE_URL + "/courseQuery/getCurriculmByForm.do"
    # AddToPlan              = _CONTROLLER_BASE_URL + "/courseQuery/addToPlan.do"
    # DeleElecPlanCurriclum  = _CONTROLLER_BASE_URL + "/electivePlan/deleElecPlanCurriclum.do"
    DrawServlet            = _BASE_URL + "/DrawServlet"
    Validate               = _CONTROLLER_BASE_URL + "/supplement/validate.do"
