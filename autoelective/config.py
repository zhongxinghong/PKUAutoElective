#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: config.py
# modified: 2019-09-10

__all__ = ["AutoElectiveConfig"]

import os
from configparser import RawConfigParser
from .utils import Singleton
from .const import CONFIG_INI


class BaseConfig(object, metaclass=Singleton):

    CONFIG_FILE = ""
    ALLOW_NO_VALUE = True

    def __init__(self):
        if self.__class__ is __class__:
            raise NotImplementedError
        file = os.path.normpath(os.path.abspath(self.__class__.CONFIG_FILE))
        if not os.path.exists(file):
            raise FileNotFoundError("config file was not found: %s" % file)
        self._config = RawConfigParser(allow_no_value=self.__class__.ALLOW_NO_VALUE)
        self._config.read(file, encoding="utf-8-sig") # 必须显示指明 encoding

    def get(self, section, key):
        return self._config.get(section, key)

    def getint(self, section, key):
        return self._config.getint(section, key)

    def getfloat(self, section, key):
        return self._config.getfloat(section, key)

    def getboolean(self, section, key):
        return self._config.getboolean(section, key)


class AutoElectiveConfig(BaseConfig):

    CONFIG_FILE = CONFIG_INI


    # MAKR: value constraints

    ALLOWED_IDENTIFY = ("bzx","bfx")
    ALLOWED_CSV_CODING = ("utf-8","gbk")


    # MAKR: model

    # [coding]

    @property
    def csvCoding(self):
        return self.get("coding", "csv_coding")

    # [user]

    @property
    def iaaaID(self):
        return self.get("user", "student_ID")

    @property
    def iaaaPassword(self):
        return self.get("user", "password")

    @property
    def isDualDegree(self):
        return self.getboolean("user", "dual_degree")

    @property
    def identity(self):
        return self.get("user", "identity")

    # [client]

    @property
    def supplyCancelPage(self):
        return self.getint("client", "supply_cancel_page")

    @property
    def refreshInterval(self):
        return self.getfloat("client", "refresh_interval")

    @property
    def refreshRandomDeviation(self):
        return self.getfloat("client", "random_deviation")

    @property
    def iaaaClientTimeout(self):
        return self.getfloat("client", "iaaa_client_timeout")

    @property
    def electiveClientTimeout(self):
        return self.getfloat("client", "elective_client_timeout")

    @property
    def electiveClientPoolSize(self):
        return self.getint("client", "elective_client_pool_size")

    @property
    def loginLoopInterval(self):
        return self.getfloat("client", "login_loop_interval")

    @property
    def isDebugPrintRequest(self):
        return self.getboolean("client", "debug_print_request")

    @property
    def isDebugDumpRequest(self):
        return self.getboolean("client", "debug_dump_request")

    # [monitor]

    @property
    def monitorHost(self):
        return self.get("monitor", "host")

    @property
    def monitorPort(self):
        return self.getint("monitor", "port")

    # MAKR: methods

    def check_csv_coding(self, coding):
        limited = self.__class__.ALLOWED_CSV_CODING
        if coding not in limited:
            raise ValueError("unsupported csv coding %s, csv coding must be in %s" % (coding, limited))

    def check_identify(self, identity):
        limited = self.__class__.ALLOWED_IDENTIFY
        if identity not in limited:
            raise ValueError("unsupported identity %s for elective, identity must be in %s" % (identity, limited))

    def check_supply_cancel_page(self, page):
        if page <= 0:
            raise ValueError("supply_cancel_page must be positive number, not %s" % page)

    def get_user_subpath(self):
        if self.isDualDegree:
            identity = self.identity
            self.check_identify(identity)

            if identity == "bfx":
                return "%s_%s" % (self.iaaaID, identity)

        return self.iaaaID
