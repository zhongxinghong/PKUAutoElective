#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: logger.py
# modified: 2019-09-09

__all__ = ["ConsoleLogger","FileLogger"]

import os
import datetime
import logging
from .config import AutoElectiveConfig
from .const import ERROR_LOG_DIR
from ._internal import mkdir


class BaseLogger(object):

    LEVEL  = logging.DEBUG
    FORMAT = logging.Formatter("[%(levelname)s] %(name)s, %(asctime)s, %(message)s", "%H:%M:%S")

    def __init__(self, name):
        if self.__class__ is __class__:
            raise NotImplementedError
        self._name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.__class__.LEVEL)
        self._logger.addHandler(self._get_headler())

    @property
    def name(self):
        return self._name

    @property
    def handlers(self):
        return self._logger.handlers

    def _get_headler(self):
        raise NotImplementedError

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


class ConsoleLogger(BaseLogger):
    """ 控制台日志输出类 """

    LEVEL = logging.DEBUG

    def _get_headler(self):
        headler = logging.StreamHandler()
        headler.setLevel(self.__class__.LEVEL)
        headler.setFormatter(self.__class__.FORMAT)
        return headler


class FileLogger(BaseLogger):
    """ 文件日志输出类 """

    LEVEL = logging.WARNING

    def _get_headler(self):
        config = AutoElectiveConfig()

        USER_ERROR_LOG_DIR = os.path.join(ERROR_LOG_DIR, config.get_user_subpath())
        mkdir(USER_ERROR_LOG_DIR)

        filename = "%s.%s.log" % (
            self.name,
            datetime.date.strftime(datetime.date.today(), "%Y%m%d")
        )
        file = os.path.join(USER_ERROR_LOG_DIR, filename)
        headler = logging.FileHandler(file, encoding="utf-8-sig")
        headler.setLevel(self.__class__.LEVEL)
        headler.setFormatter(self.__class__.FORMAT)
        return headler
