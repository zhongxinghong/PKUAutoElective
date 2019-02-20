#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: hook.py

import re
from .logger import ConsoleLogger
from .parser import get_tree_from_response, get_title, get_errInfo, get_tips
from .exceptions import StatusCodeError, ServerError, IAAANotSuccessError, SystemException,\
    InvalidTokenError, InvalidSessionError, CaughtCheatingError, InvalidOperatingTimeError,\
    CourseIndexError, CaptchaError, TipsException, ConflictingTimeError, RepeatedElectionError,\
    OperationTimedOutError, ElectivePermissionError, ElectionSuccess, ElectionFailedError,\
    CreditLimitedError, MutuallyExclusiveCourseError, NoAuthInfoError, SharedSessionError


__all__ = [

    "get_hooks",
    'merge_hooks',

    "with_etree",
    "del_etree",

    "check_status_code",

    "check_iaaa_success",
    "check_elective_title",
    "check_elective_tips",

    "print_request_status",

    ]

__logger = ConsoleLogger("hook")

#__regex_errInfo = re.compile(r"<strong>出错提示:</strong>(\S+?)<br>", re.S)
__regex_errOperatingTime = re.compile(r'目前不是(\S+?)时间，因此不能进行相应操作。')
__regex_electionSuccess = re.compile(r'补选课程(\S+)成功，请查看已选上列表确认，并查看选课结果。')
__regex_mutex = re.compile(r'(\S+)与(\S+)只能选其一门。')

def get_hooks(*fn):
    return {"response": fn}

def merge_hooks(hooks, *fn):
    return {"response": hooks["response"] + fn}

def with_etree(r, **kwargs):
    r._tree = get_tree_from_response(r)

def del_etree(r, **kwargs):
    del r._tree

def check_status_code(r, **kwargs):
    if r.status_code != 200:
        if r.status_code in {301,302,304}:
            pass
        elif r.status_code in {500,501,502,503}:
            raise ServerError(response=r)
        else:
            raise StatusCodeError(response=r)

def check_iaaa_success(r, **kwargs):
    _json = r.json()
    if not _json.get("success"):
        raise IAAANotSuccessError(response=r)

def check_elective_title(r, **kwargs):
    assert hasattr(r, "_tree")
    title = get_title(r._tree)
    if title is None:
        pass
    elif title == "系统异常":
        #err = __regex_errInfo.search(r.text).group(1)
        err = get_errInfo(r._tree)
        if err == "token无效": # sso_login 时出现
            raise InvalidTokenError(response=r)
        elif err == "您尚未登录或者会话超时,请重新登录.":
            raise InvalidSessionError(response=r)
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
        elif __regex_errOperatingTime.search(err):
            raise InvalidOperatingTimeError(response=r, msg=err)
        else:
            raise SystemException(response=r, msg=err)

def check_elective_tips(r, **kwargs):
    assert hasattr(r, "_tree")
    tips = get_tips(r._tree)
    if tips is None:
        pass
    elif tips == "您已经选过该课程了。":
        raise RepeatedElectionError(response=r)
    elif tips == "对不起，超时操作，请重新登录。":
        raise OperationTimedOutError(response=r)
    elif tips == "选课操作失败，请稍后再试。":
        raise ElectionFailedError(response=r)
    elif tips == "您本学期所选课程的总学分已经超过规定学分上限。":
        raise CreditLimitedError(response=r)
    elif tips.startswith("上课时间冲突："):
        raise ConflictingTimeError(response=r, msg=tips)
    elif tips.startswith("该课程在补退选阶段开始后的约一周开放选课"): # 这个可能需要根据当学期情况进行修改
        raise ElectivePermissionError(response=r, msg=tips)
    elif __regex_electionSuccess.search(tips):
        raise ElectionSuccess(response=r, msg=tips)
    elif __regex_mutex.search(tips):
        raise MutuallyExclusiveCourseError(response=r, msg=tips)
    else:
        __logger.warning("Unknown tips: %s" % tips)
        pass
        #raise TipsException(response=r, msg=tips)

def print_request_info(r, **kwargs):
    __logger.debug("url: %s" % r.url)
