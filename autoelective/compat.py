#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: compat.py
# modified: 2019-09-08

__all__ = ["install_ctrl_c_handler"]

import sys
import signal


def _handler_ctrl_c(sig, frame):
    raise KeyboardInterrupt

def install_ctrl_c_handler():
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, _handler_ctrl_c)
