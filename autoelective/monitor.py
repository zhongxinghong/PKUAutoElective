#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: monitor.py
# modified: 2019-09-17

import importlib
from .config import AutoElectiveConfig
from .logger import ConsoleLogger, FileLogger


config = AutoElectiveConfig()
cout = ConsoleLogger("monitor")
ferr = FileLogger("monitor.error")


def run_monitor():
    cout.info(config.monitor_type + ' monitor start!')
    monitor = importlib.import_module('autoelective.monitors.'+config.monitor_type)
    monitor.run()
