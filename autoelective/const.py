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

CNN_MODEL_FILE          = absp("./captcha/model/cnn.pt.gz")
USER_AGENTS_TXT         = absp("../user_agents.txt")
USER_AGENTS_USER_TXT    = absp("../user_agents.user.txt")
DEFAULT_CONFIG_INI      = absp("../config.ini")

mkdir(CACHE_DIR)
mkdir(CAPTCHA_CACHE_DIR)
mkdir(LOG_DIR)
mkdir(ERROR_LOG_DIR)
mkdir(REQUEST_LOG_DIR)


# 警惕直接复制的 User-Agent 中可能存在的省略号（例如源自 Firefox 开发者工具），它可能会引发如下错误：
#   File "/usr/lib/python3.6/http/client.py", line 1212, in putheader
#     values[i] = one_value.encode('latin-1')
# UnicodeEncodeError: 'latin-1' codec can't encode character '\u2026' in position 30: ordinal not in range(256)
USER_AGENT_LIST = read_list(USER_AGENTS_USER_TXT) if os.path.exists(USER_AGENTS_USER_TXT) \
                    else read_list(USER_AGENTS_TXT)


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
    SSOLoginDualDegree      sso登录（双学位）
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
    SSOLoginRedirect = "http://elective.pku.edu.cn:80/elective2008/ssoLogin.do"
    SSOLogin         = "https://elective.pku.edu.cn/elective2008/ssoLogin.do"
    Logout           = "https://elective.pku.edu.cn/elective2008/logout.do"
    HelpController   = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/help/HelpController.jpf"
    ShowResults      = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/electiveWork/showResults.do"
    SupplyCancel     = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/SupplyCancel.do"
    Supplement       = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/supplement.jsp"
    DrawServlet      = "https://elective.pku.edu.cn/elective2008/DrawServlet"
    Validate         = "https://elective.pku.edu.cn/elective2008/edu/pku/stu/elective/controller/supplement/validate.do"
