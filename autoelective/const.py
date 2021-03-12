#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: const.py
# modified: 2019-09-11

import os
from ._internal import mkdir, absp, read_list

CACHE_DIR               = absp("../cache/")
CAPTCHA_CACHE_DIR       = absp("../cache/captcha/")
LOG_DIR                 = absp("../log/")
ERROR_LOG_DIR           = absp("../log/error")
REQUEST_LOG_DIR         = absp("../log/request/")
WEB_LOG_DIR             = absp("../log/web/")

CNN_MODEL_FILE          = absp("../model/cnn.20210311.1.pt")
USER_AGENTS_TXT_GZ      = absp("../user_agents.txt.gz")
USER_AGENTS_USER_TXT    = absp("../user_agents.user.txt")
DEFAULT_CONFIG_INI      = absp("../config.ini")

mkdir(CACHE_DIR)
mkdir(CAPTCHA_CACHE_DIR)
mkdir(LOG_DIR)
mkdir(ERROR_LOG_DIR)
mkdir(REQUEST_LOG_DIR)
mkdir(WEB_LOG_DIR)

if os.path.exists(USER_AGENTS_USER_TXT):
    USER_AGENT_LIST = read_list(USER_AGENTS_USER_TXT)
else:
    USER_AGENT_LIST = read_list(USER_AGENTS_TXT_GZ)


class IAAAURL(object):
    """
    Host
    OauthHomePage
    OauthLogin
    """
    Host          = "iaaa.pku.edu.cn"
    OauthHomePage = "https://iaaa.pku.edu.cn/iaaa/oauth.jsp"
    OauthLogin    = "https://iaaa.pku.edu.cn/iaaa/oauthlogin.do"


class ElectiveURL(object):
    """
    Host
    SSOLoginRedirect        重定向链接
    SSOLogin                sso登录
    Logout                  登出
    HelpController          选课帮助页
    ShowResults             选课结果页
    SupplyCancel            补退选页
    Supplement              补退选页第一页之后
    DrawServlet             获取一张验证码
    validate                补退选验证码校验接口
    """
    Scheme           = "https"
    Host             = "elective.pku.edu.cn"
    HomePage         = "https://elective.pku.edu.cn/elective2008/"
    SSOLoginRedirect = "http://elective.pku.edu.cn:80/elective2008/ssoLogin.do"
    SSOLogin         = "https://elective.pku.edu.cn/elective2008/ssoLogin.do"
    Logout           = "https://elective.pku.edu.cn/elective2008/logout.do"
    HelpController   = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/help/HelpController.jpf"
    ShowResults      = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/electiveWork/showResults.do"
    SupplyCancel     = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do"
    Supplement       = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/supplement.jsp"
    DrawServlet      = "https://elective.pku.edu.cn/elective2008/DrawServlet"
    Validate         = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/validate.do"
