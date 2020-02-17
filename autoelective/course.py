#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: course.py
# modified: 2019-09-08

class Course(object):

    __slots__ = ['_name','_class_no','_school','_status','_href','_ident']

    def __init__(self, name, class_no, school, status=None, href=None):
        self._name = name
        self._class_no = int(class_no) # 确保 01 与 1 为同班号，因为表格软件将 01 视为 1
        self._school = school
        self._status = status # (limit, current) 限选 / 已选
        self._href = href     # 选课链接
        self._ident = (name, class_no, school)

    @property
    def name(self):
        return self._name

    @property
    def class_no(self):
        return self._class_no

    @property
    def school(self):
        return self._school

    @property
    def status(self):
        return self._status

    @property
    def href(self):
        return self._href

    def is_available(self):
        if self._status is None:
            return False
        limit, current = self._status
        return limit > current

    def to_simplified(self):
        return Course(self._name, self._class_no, self._school)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._ident == other._ident

    def __hash__(self):
        return hash(self._ident)

    def __repr__(self):
        if self._status is not None:
            return "%s(%s, %s, %s, %d / %d)" % (
                self.__class__.__name__,
                self._name, self._class_no, self._school, *self._status,
            )
        else:
            return "%s(%s, %s, %s)" % (
                self.__class__.__name__,
                self._name, self._class_no, self._school,
            )
