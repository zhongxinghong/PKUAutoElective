#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: environ.py
# modified: 2020-02-16

from .utils import Singleton
from collections import defaultdict
import numpy as np

class Environ(object, metaclass=Singleton):

    __slots__ = [
        'config_ini',
        'with_monitor',
        'iaaa_loop',
        'elective_loop',
        'errors',
        'iaaa_loop_thread',
        'elective_loop_thread',
        'monitor_thread',
        'goals',
        'mutexes',
        'ignored',
    ]

    def __init__(self):
        self.config_ini = None
        self.with_monitor = None
        self.iaaa_loop = 0
        self.elective_loop = 0
        self.errors = defaultdict(lambda: 0)
        self.iaaa_loop_thread = None
        self.elective_loop_thread = None
        self.monitor_thread = None
        self.goals = []
        self.mutexes = np.zeros(0, dtype=np.uint8) # unit8 [N][N]; N = len(goals);
        self.ignored = {} # {course, reason}
