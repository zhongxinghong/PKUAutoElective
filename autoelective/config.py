#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: config.py

from configparser import RawConfigParser
from .util import Singleton
from .const import Config_INI
from .exceptions import ABCNotImplementedError

__all__ = [

    "GeneralConfig", "generalCfg",

    ]


class ConfigMixin(object, metaclass=Singleton):
    """ [配置文件类，configparser 模块的封装]

        Attributes:
            class:
                Config_File    str                配置文件绝对路径
            instance:
                _cfg       RawConfigParser    RawConfigParser 类实例
    """
    Config_File = ""
    Allow_No_Value = True

    def __init__(self):
        if self.__class__ == __class__:
            raise ABCNotImplementedError
        self._cfg = RawConfigParser(allow_no_value=self.__class__.Allow_No_Value)
        self._cfg.read(self.__class__.Config_File, encoding="utf-8-sig") # 必须显示指明 encoding

    def __getitem__(self, idx):
        """ config[] 操作运算的封装 """
        return self._cfg[idx]

    def sections(self):
        """ config.sections 函数的封装 """
        return self._cfg.sections()

    def __get(self, get_fn, section, key, **kwargs):
        """ 配置文件 get 函数模板

            Args:
                get_fn     function    原始的 config.get 函数
                section    str         section 名称
                key        str         section 下的 option 名称
                **kwargs               传入 get_fn
            Returns:
                value      str/int/float/bool   返回相应 section 下相应 key 的 value 值
        """
        value = get_fn(section, key, **kwargs)
        if value is None:
            raise ValueError("key '%s' in section [%s] is missing !" % (key, section))
        else:
            return value

    """
        以下对四个 config.get 函数进行封装

        Args:
            section    str    section 名称
            key        str    section 下的 option 名称
        Returns:
            value             以特定类型返回相应 section 下相应 key 的 value 值
    """
    def get(self, section, key):
        return self.__get(self._cfg.get, section, key)

    def getint(self, section, key):
        return self.__get(self._cfg.getint, section, key)

    def getfloat(self, section, key):
        return self.__get(self._cfg.getfloat, section, key)

    def getboolean(self, section, key):
        return self.__get(self._cfg.getboolean, section, key)


class GeneralConfig(ConfigMixin):
    """ 全局的 config """
    Config_File = Config_INI

generalCfg = GeneralConfig()