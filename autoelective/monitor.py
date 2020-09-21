#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: monitor.py
# modified: 2019-09-17

import importlib
from .config import AutoElectiveConfig
from .logger import ConsoleLogger, FileLogger
from .environ import Environ

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("monitor")
ferr = FileLogger("monitor.error")


def run_monitor():
    monitor = importlib.import_module("autoelective.monitors."+config.monitor_type)
    try:
        cout.info(config.monitor_type + ' monitor start!')
        monitor.run_monitor()
    except Exception as e:
        ferr.error(config.monitor_type + ' monitor stop!')
        ferr.error(e)
