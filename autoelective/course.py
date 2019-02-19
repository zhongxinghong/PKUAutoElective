#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: course.py

from .util import ImmutableAttrsMixin
from .exceptions import StatusNotSetError

__all__ = ["Course",]


class Course(ImmutableAttrsMixin):

    def __init__(self, name, classNo, school, status=None, href=None):
        self.name = name
        self.classNo = int(classNo) # 确保 01 与 1 为同班号，因为表格软件将 01 视为 1
        self.school = school
        self.status = status # (limit, current) 限选 / 已选
        self.href = href     # 选课链接

    def is_available(self):
        if self.status is None:
            raise StatusNotSetError
        limit, current = self.status
        return (limit > current)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (
            (self.name == other.name) and
            (self.classNo == other.classNo) and
            (self.school == other.school)
            )

    def __repr__(self):
        if self.status is not None:
            return "Course(%s, %s, %s, %d / %d)" % (
                self.name, self.classNo, self.school, *self.status)
        else:
            return "Course(%s, %s, %s)" % (
            self.name, self.classNo, self.school)


