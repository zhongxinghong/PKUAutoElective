#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: logger.py

import os
import datetime
import logging
from .util import ReadonlyProperty
from .const import Log_Dir
from .exceptions import ABCNotImplementedError

__all__ = [

    "ConsoleLogger",
    "FileLogger",

    ]


class LoggerMixin(object):

    Level  = logging.DEBUG
    #Format = logging.Formatter("[%(levelname)s] %(name)s, %(asctime)s, %(message)s", "%Y-%m-%d %H:%M:%S")
    Format = logging.Formatter("[%(levelname)s] %(name)s, %(asctime)s, %(message)s", "%H:%M:%S")

    def __init__(self, name):
        if self.__class__ is __class__:
            raise ABCNotImplementedError
        self.__name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.__class__.Level)
        self._logger.addHandler(self._get_headler())

    @ReadonlyProperty
    def name(self):
        return self.__name

    def _get_headler(self):
        raise NotImplementedError

    """ 以下是对 logging 的各种日志等级常数的封装 """

    @ReadonlyProperty
    def NOTSET(self):
        return logging.NOTSET

    @ReadonlyProperty
    def DEBUG(self):
        return logging.DEBUG

    @ReadonlyProperty
    def INFO(self):
        return logging.INFO

    @ReadonlyProperty
    def WARN(self):
        return logging.WARN

    @ReadonlyProperty
    def WARNING(self):
        return logging.WARNING

    @ReadonlyProperty
    def ERROR(self):
        return logging.ERROR

    @ReadonlyProperty
    def FATAL(self):
        return logging.FATAL

    @ReadonlyProperty
    def CRITICAL(self):
        return logging.CRITICAL

    """ 以下是对 logging 的各种输出函数的封装 """

    def log(self, level, msg, *args, **kwargs):
        return self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        return self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return self._logger.info(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        return self._logger.warn(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self._logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        kwargs.setdefault("exc_info", True)
        return self._logger.exception(msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        return self._logger.fatal(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        return self._logger.critical(msg, *args, **kwargs)



class ConsoleLogger(LoggerMixin):
    """ 控制台日志输出类 """

    Level = logging.DEBUG

    def _get_headler(self):
        """ 返回封装好的 console_headler """
        headler = logging.StreamHandler()
        headler.setLevel(self.__class__.Level)
        headler.setFormatter(self.__class__.Format)
        return headler


class FileLogger(LoggerMixin):
    """ 文件日志输出类 """

    Level = logging.WARNING

    def _get_headler(self):
        """ 返回封装好的  """
        filename = "%s.%s.log" % (
            self.name,
            datetime.date.strftime(datetime.date.today(), "%Y%m%d")
            )
        path = os.path.join(Log_Dir, filename)
        headler = logging.FileHandler(path, encoding="utf-8")
        headler.setLevel(self.__class__.Level)
        headler.setFormatter(self.__class__.Format)
        return headler
