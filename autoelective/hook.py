#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: hook.py
# modified: 2019-09-11

import os
import re
import time
from urllib.parse import quote, urlparse
from .logger import ConsoleLogger
from .config import AutoElectiveConfig
from .parser import get_tree_from_response, get_title, get_errInfo, get_tips
from .utils import pickle_gzip_dump
from .const import REQUEST_LOG_DIR
from .exceptions import *
from ._internal import mkdir

cout = ConsoleLogger("hook")
config = AutoElectiveConfig()

_USER_REQUEST_LOG_DIR = os.path.join(REQUEST_LOG_DIR, config.get_user_subpath())
mkdir(_USER_REQUEST_LOG_DIR)

_regexErrorOperatingTime = re.compile(r'目前不是(.*?)时间，因此不能进行相应操作。')
_regexElectionSuccess    = re.compile(r'补选（或者候补）课程(.*)成功，请查看已选上列表确认，并查看选课结果。')
_regexMutex              = re.compile(r'(.+)与(.+)只能选其一门。')

_DUMMY_HOOK = {"response": []}


def get_hooks(*fn):
    return {"response": fn}

def merge_hooks(*hooklike):
    funcs = []
    for hook in hooklike:
        if isinstance(hook, dict):
            funcs.extend(hook["response"])
        elif callable(hook): # function
            funcs.append(hook)
        else:
            raise TypeError(hook)
    return get_hooks(*funcs)

def with_etree(r, **kwargs):
    r._tree = get_tree_from_response(r)

def del_etree(r, **kwargs):
    del r._tree


def check_status_code(r, **kwargs):
    if r.status_code != 200:
        if r.status_code in (301,302,304):
            pass
        elif r.status_code in (500,501,502,503):
            raise ServerError(response=r)
        else:
            raise StatusCodeError(response=r)


def check_iaaa_success(r, **kwargs):
    respJson = r.json()

    if not respJson.get("success", False):
        try:
            errors = respJson["errors"]
            code = errors["code"]
            msg = errors["msg"]
        except Exception as e:
            cout.error(e)
            cout.info("Unable to get errcode/errmsg from response JSON")
            pass
        else:
            if code == "E01":
                raise IAAAIncorrectPasswordError(response=r, msg=msg)
            elif code == "E21":
                raise IAAAForbiddenError(response=r, msg=msg)

        raise IAAANotSuccessError(response=r)


def check_elective_title(r, **kwargs):
    assert hasattr(r, "_tree")

    title = get_title(r._tree)
    if title is None:
        return

    try:
        if title in ("系统异常", "系统提示"):
            err = get_errInfo(r._tree)

            if err == "token无效": # sso_login 时出现
                raise InvalidTokenError(response=r)

            elif err == "您尚未登录或者会话超时,请重新登录.":
                raise SessionExpiredError(response=r)

            elif err == "请不要用刷课机刷课，否则会受到学校严厉处分！":
                raise CaughtCheatingError(response=r)

            elif err == "索引错误。":
                raise CourseIndexError(response=r)

            elif err == "验证码不正确。":
                raise CaptchaError(response=r)

            elif err == "无验证信息。":
                raise NoAuthInfoError(response=r)

            elif err == "你与他人共享了回话，请退出浏览器重新登录。":
                raise SharedSessionError(response=r)

            elif err == "只有同意选课协议才可以继续选课！":
                raise NotAgreedToSelectionAgreement(response=r)

            elif _regexErrorOperatingTime.search(err):
                raise NotInOperationTimeError(response=r, msg=err)

            else:
                raise SystemException(response=r, msg=err)

    except Exception as e:
        if "_client" in r.request.__dict__:  # _client will be set by BaseClient
            r.request._client.persist_cookies(r)
        raise e


def check_elective_tips(r, **kwargs):
    assert hasattr(r, "_tree")
    tips = get_tips(r._tree)

    try:

        if tips is None:
            return

        elif tips == "您已经选过该课程了。":
            raise ElectionRepeatedError(response=r)

        elif tips == "对不起，超时操作，请重新登录。":
            raise OperationTimeoutError(response=r)

        elif tips == "选课操作失败，请稍后再试。":
            raise ElectionFailedError(response=r)

        elif tips == "您本学期所选课程的总学分已经超过规定学分上限。":
            raise CreditsLimitedError(response=r)

        elif tips == "学校规定每学期只能修一门英语课，因此您不能选择该课。":
            raise MultiEnglishCourseError(response=r)

        elif tips.startswith("上课时间冲突"):
            raise TimeConflictError(response=r, msg=tips)

        elif tips.startswith("考试时间冲突"):
            raise ExamTimeConflictError(response=r, msg=tips)

        elif tips.startswith("该课程在补退选阶段开始后的约一周开放选课"): # 这个可能需要根据当学期情况进行修改
            raise ElectionPermissionError(response=r, msg=tips)

        elif tips.startswith("该课程选课人数已满"):
            raise QuotaLimitedError(response=r, msg=tips)

        elif tips.startswith("学校规定每学期只能修一门体育课"):
            raise MultiPECourseError(response=r, msg=tips)

        elif _regexElectionSuccess.search(tips):
            raise ElectionSuccess(response=r, msg=tips)

        elif _regexMutex.search(tips):
            raise MutexCourseError(response=r, msg=tips)

        else:
            cout.warning("Unknown tips: %s" % tips)
            # raise TipsException(response=r, msg=tips)

    except Exception as e:
        if "_client" in r.request.__dict__:  # _client will be set by BaseClient
            r.request._client.persist_cookies(r)
        raise e


def debug_print_request(r, **kwargs):
    if not config.is_debug_print_request:
        return
    cout.debug("> %s  %s" % (r.request.method, r.url))
    cout.debug("> Headers:")
    for k, v in r.request.headers.items():
        cout.debug("%s: %s" % (k, v))
    cout.debug("> Body:")
    cout.debug(r.request.body)
    cout.debug("> Response Headers:")
    for k, v in r.headers.items():
        cout.debug("%s: %s" % (k, v))
    cout.debug("")


def _dump_request(r):
    if "_client" in r.request.__dict__:  # _client will be set by BaseClient
        client = r.request._client
        r.request._client = None  # don't save client object

    hooks = r.request.hooks
    r.request.hooks = _DUMMY_HOOK  # don't save hooks array

    timestamp = time.strftime("%Y-%m-%d_%H.%M.%S%z")
    basename = quote(urlparse(r.url).path, '')
    filename = "%s.%s.gz" % (timestamp, basename)  # put timestamp first
    file = os.path.normpath(os.path.abspath(os.path.join(_USER_REQUEST_LOG_DIR, filename)))

    pickle_gzip_dump(r, file)

    # restore objects defined by autoelective package
    if "_client" in r.request.__dict__:
        r.request._client = client
    r.request.hooks = hooks

    return file


def debug_dump_request(r, **kwargs):
    if not config.is_debug_dump_request:
        return
    file = _dump_request(r)
    cout.debug("Dump request %s to %s" % (r.url, file))
