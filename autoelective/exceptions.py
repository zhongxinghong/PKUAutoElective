#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: exceptions.py
# modified: 2019-09-13

__all__ = [

"AutoElectiveException",

    "UserInputException",

    "AutoElectiveClientException",

        "StatusCodeError",
        "ServerError",
        "OperationFailedError",
        "UnexceptedHTMLFormat",

        "IAAAException",
            "IAAANotSuccessError",
                "IAAAIncorrectPasswordError",
                "IAAAForbiddenError",

        "ElectiveException",

            "SystemException",
                "CaughtCheatingError",
                "InvalidTokenError",
                "SessionExpiredError",
                "NotInOperationTimeError",
                "CourseIndexError",
                "CaptchaError",
                "NoAuthInfoError",
                "SharedSessionError",
                "NotAgreedToSelectionAgreement",

            "TipsException",
                "ElectionSuccess",
                "ElectionRepeatedError",
                "TimeConflictError",
                "OperationTimeoutError",
                "ElectionPermissionError",
                "ElectionFailedError",
                "CreditsLimitedError",
                "MutexCourseError",
                "MultiEnglishCourseError",
                "ExamTimeConflictError",
                "QuotaLimitedError",
                "MultiPECourseError",

]


class AutoElectiveException(Exception):
    """ Abstract Exception for AutoElective """

class UserInputException(AutoElectiveException, ValueError):
    """ 由于用户的输入数据不当而引发的错误 """


class AutoElectiveClientException(AutoElectiveException):

    code = -1
    desc = "AutoElectiveException"

    def __init__(self, *args, **kwargs):
        response = kwargs.pop("response", None)
        self.response = response
        msg = "[%d] %s" % (
            self.__class__.code,
            kwargs.pop("msg", self.__class__.desc)
        )
        super().__init__(msg, *args, **kwargs)


class StatusCodeError(AutoElectiveClientException):
    code = 101
    desc = "response.status_code != 200"

    def __init__(self, *args, **kwargs):
        r = kwargs.get("response")
        if r is not None and "msg" not in kwargs:
            kwargs["msg"] = "%s. response status code: %s" % (self.__class__.code, r.status_code)
        super().__init__(*args, **kwargs)

class ServerError(AutoElectiveClientException):
    code = 102
    desc = r"response.status_code in (500, 501, 502, 503)"

    def __init__(self, *args, **kwargs):
        r = kwargs.get("response")
        if r is not None and "msg" not in kwargs:
            kwargs["msg"] = "%s. response status_code: %s" % (self.__class__.code, r.status_code)
        super().__init__(*args, **kwargs)

class OperationFailedError(AutoElectiveClientException):
    code = 103
    desc = r"some operations failed for unknown reasons"

class UnexceptedHTMLFormat(AutoElectiveClientException):
    code = 104
    desc = r"unable to parse HTML content"


class IAAAException(AutoElectiveClientException):
    code = 200
    desc = "IAAAException"


class IAAANotSuccessError(IAAAException):
    code = 210
    desc = "response.json()['success'] == False"

    def __init__(self, *args, **kwargs):
        r = kwargs.get("response")
        if r is not None and "msg" not in kwargs:
            kwargs["msg"] = "%s. response JSON: %s" % (self.__class__.code, r.json())
        super().__init__(*args, **kwargs)

class IAAAIncorrectPasswordError(IAAANotSuccessError):
    code = 211
    desc = "User ID or Password is incorrect"

class IAAAForbiddenError(IAAANotSuccessError):
    code = 212
    desc = "You are FORBIDDEN. Please sign in after a half hour"


class ElectiveException(AutoElectiveClientException):
    code = 300
    desc = "ElectiveException"


class SystemException(ElectiveException):
    code = 310
    desc = "<title>系统异常</title>"

class CaughtCheatingError(SystemException):
    code = 311
    desc = "请不要用刷课机刷课，否则会受到学校严厉处分！" # 没有设 referer

class InvalidTokenError(SystemException):
    code = 312
    desc = "Token无效" # sso_login 时出现，在上次登录前发生异地登录，缓存 token 失效

class SessionExpiredError(SystemException):
    code = 313
    desc = "您尚未登录或者会话超时,请重新登录." # 相当于 token 失效

class NotInOperationTimeError(SystemException):
    code = 314
    desc = "不在操作时段"

class CourseIndexError(SystemException):
    code = 315
    desc = "索引错误。"

class CaptchaError(SystemException):
    code = 316
    desc = "验证码不正确。"

class NoAuthInfoError(SystemException):
    code = 317
    desc = "无验证信息。" # 仅辅双登录时会出现

class SharedSessionError(SystemException):
    code = 318
    desc = "你与他人共享了回话，请退出浏览器重新登录。"

class NotAgreedToSelectionAgreement(SystemException):
    code = 319
    desc = "只有同意选课协议才可以继续选课！ "


class TipsException(ElectiveException):
    code = 330
    desc = "TipsException"

class ElectionSuccess(TipsException):
    code = 331
    desc = "补选课程成功，请查看已选上列表确认，并查看选课结果。"

class ElectionRepeatedError(TipsException):
    code = 332
    desc = "您已经选过该课程了。"

class TimeConflictError(TipsException):
    code = 333
    desc = "上课时间冲突"

class OperationTimeoutError(TipsException):
    code = 334
    desc = "对不起，超时操作，请重新登录。"

class ElectionPermissionError(TipsException):
    code = 335
    desc = "该课程在补退选阶段开始后的约一周开放选课"

class ElectionFailedError(TipsException):
    code = 336
    desc = "选课操作失败，请稍后再试。"

class CreditsLimitedError(TipsException):
    code = 327
    desc = "您本学期所选课程的总学分已经超过规定学分上限。"

class MutexCourseError(TipsException):
    code = 328
    desc = "只能选其一门。"

class MultiEnglishCourseError(TipsException):
    code = 329
    desc = "学校规定每学期只能修一门英语课，因此您不能选择该课。"

class ExamTimeConflictError(TipsException):
    code = 330
    desc = "考试时间冲突"

class QuotaLimitedError(TipsException):
    code = 331
    desc = "该课程选课人数已满。"

class MultiPECourseError(TimeoutError):
    code = 332
    desc = "学校规定每学期只能修一门体育课。"
