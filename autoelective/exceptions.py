#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: exceptions.py

__all__ = [

"AutoElectiveException",

    "ABCNotImplementedError",
    "ImmutableTypeError",
    "ReadonlyPropertyError",
    "NoInstanceError",
    "StatusNotSetError",

    "ModelFileNotFoundError",
    "FeatureCodeError",

    "ImageProcessorException",
        "ImageModeError",
        "ImageBlocksNumException",

    "UserInputException",
        "NotInCoursePlanException",
        "UnsupportedCodingError",
        "UnsupportedIdentityError",

    "AutoElectiveClientException",

        "NoException",
        "StatusCodeError",
        "ServerError",

        "IAAAException",
            "IAAANotSuccessError",

        "ElectiveException",

            "SystemException",
                "InvalidTokenError",
                "InvalidSessionError",
                "InvalidOperatingTimeError",
                "CourseIndexError",
                "CaptchaError",
                "NoAuthInfoError",
                "SharedSessionError",

            "TipsException",
                "ElectionSuccess",
                "RepeatedElectionError",
                "ConflictingTimeError",
                "OperationTimedOutError",
                "ElectivePermissionError",
                "ElectionFailedError",
                "CreditLimitedError",
                "MutuallyExclusiveCourseError",
                "MultiEnglishCourseError",

]


class AutoElectiveException(Exception):
    """ 抽象基类 """


class ABCNotImplementedError(AutoElectiveException, NotImplementedError):
    """ 抽象基类实例化 """

class ImmutableTypeError(AutoElectiveException, TypeError):
    """ 修改了不可变对象 """

class ReadonlyPropertyError(AutoElectiveException):
    """ 尝试修改只读属性 """

class NoInstanceError(AutoElectiveException):
    """ noinstance 修饰的类被实例化 """

class StatusNotSetError(AutoElectiveException):
    """ 课程未设置 status 但被使用 """


class ModelFileNotFoundError(AutoElectiveException, FileNotFoundError):
    """ model 文件丢失 """

class FeatureCodeError(AutoElectiveException, KeyError):
    """ 未知的特征提取函数的代号 """


class ImageProcessorException(AutoElectiveException):
    """ 图像处理库错误基类 """

class ImageModeError(ImageProcessorException):
    """ 模式非 "1" """

class ImageBlocksNumException(ImageProcessorException):
    """ 分割块数量应该的介于 [1,4] """


class UserInputException(AutoElectiveException):
    """ csv 与 config.ini 等输入数据有误 """

class NotInCoursePlanException(UserInputException):
    """ csv 内指定的课程不在选课计划内 """

class UnsupportedCodingError(UserInputException):
    """ 不支持的编码格式 """

class UnsupportedIdentityError(UserInputException):
    """ 不支持的双学位登录身份 """


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


class NoException(AutoElectiveClientException):
    code = 0
    desc = "success"

class StatusCodeError(AutoElectiveClientException):
    code = 101
    desc = "response.status_code != 200"

class ServerError(AutoElectiveClientException):
    code = 102
    desc = r"response.status_code in {500, 501, 502, 503}"

class IAAAException(AutoElectiveClientException):
    code = 200
    desc = "IAAAException"

class IAAANotSuccessError(IAAAException):
    code = 201
    desc = "response.json()['success'] == False"


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

class InvalidSessionError(SystemException):
    code = 313
    desc = "您尚未登录或者会话超时,请重新登录." # 相当于 token 失效

class InvalidOperatingTimeError(SystemException):
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


class TipsException(ElectiveException):
    code = 330
    desc = "TipsException"

class ElectionSuccess(TipsException):
    code = 331
    desc = "补选课程成功，请查看已选上列表确认，并查看选课结果。"

class RepeatedElectionError(TipsException):
    code = 332
    desc = "您已经选过该课程了。"

class ConflictingTimeError(TipsException):
    code = 333
    desc = "上课时间冲突"

class OperationTimedOutError(TipsException):
    code = 334
    desc = "对不起，超时操作，请重新登录。"

class ElectivePermissionError(TipsException):
    code = 335
    desc = "该课程在补退选阶段开始后的约一周开放选课"

class ElectionFailedError(TipsException):
    code = 336
    desc = "选课操作失败，请稍后再试。"

class CreditLimitedError(TipsException):
    code = 327
    desc = "您本学期所选课程的总学分已经超过规定学分上限。"

class MutuallyExclusiveCourseError(TipsException):
    code = 328
    desc = "只能选其一门。"

class MultiEnglishCourseError(TipsException):
    code = 329
    desc = "学校规定每学期只能修一门英语课，因此您不能选择该课。"