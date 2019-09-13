#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: parser.py
# modified: 2019-09-09

__all__ = [

    "get_tree_from_response",
    "get_tree",
    "get_tables",
    "get_table_header",
    "get_table_trs",
    "get_title",
    "get_errInfo",
    "get_tips",

    "get_courses",
    "get_courses_with_detail",

    "load_course_csv",

    ]

import re
from lxml import etree
from .course import Course
from .config import AutoElectiveConfig
from .utils import read_csv
from .const import DEFAULT_COURSE_UTF8_CSV, DEFAULT_COURSE_GBK_CSV
from ._internal import userInfo


_regexBzfxSida = re.compile(r'\?sida=(\S+?)&sttp=(?:bzx|bfx)')


def get_tree_from_response(r):
    return etree.HTML(r.text) # 不要用 r.content, 否则可能会以 latin-1 编码

def get_tree(content):
    return etree.HTML(content)

def get_tables(tree):
    return tree.xpath('.//table//table[@class="datagrid"]')

def get_table_header(table):
    return table.xpath('.//tr[@class="datagrid-header"]/th/text()')

def get_table_trs(table):
    return table.xpath('.//tr[@class="datagrid-odd" or @class="datagrid-even"]')

def get_title(tree):
    title = tree.find('.//head/title')
    if title is not None: # 双学位 sso_login 后先到 主修/辅双 选择页，这个页面没有 title 标签
        return title.text
    else:
        return None

def get_errInfo(tree):
    tds = tree.xpath(".//table//table//table//td")
    assert len(tds) == 1
    td = tds[0]
    strong = td.getchildren()[0]
    assert strong.tag == 'strong' and strong.text == '出错提示:'
    return "".join(td.xpath('./text()')).strip()

def get_tips(tree):
    tips = tree.xpath('.//td[@id="msgTips"]')
    if len(tips) == 0:
        return None
    else:
        td = tips[0].xpath('.//table//table//td')[1]
        return "".join(td.xpath('.//text()')).strip()

def get_sida(r):
    return _regexBzfxSida.search(r.text).group(1)

def get_courses(table):
    header = get_table_header(table)
    trs = get_table_trs(table)
    idxs = tuple(map(header.index, ["课程名","班号","开课单位"]))
    cs = []
    for tr in trs:
        t = tr.xpath('./th | ./td')
        name, classNo, school = map(lambda i: t[i].xpath('.//text()')[0], idxs)
        c = Course(name, classNo, school)
        cs.append(c)
    return cs

def get_courses_with_detail(table):
    header = get_table_header(table)
    trs = get_table_trs(table)
    idxs = tuple(map(header.index, ["课程名","班号","开课单位","限数/已选","补选"]))
    cs = []
    for tr in trs:
        t = tr.xpath('./th | ./td')
        name, classNo, school, status, _ = map(lambda i: t[i].xpath('.//text()')[0], idxs)
        status = tuple(map(int, status.split("/")))
        href = t[idxs[-1]].xpath('./a/@href')[0]
        c = Course(name, classNo, school, status, href)
        cs.append(c)
    return cs


def load_course_csv():
    config = AutoElectiveConfig()

    coding = config.csvCoding.lower()
    config.check_csv_coding(coding)

    COURSE_UTF8_CSV = userInfo.get("COURSE_UTF8_CSV", DEFAULT_COURSE_UTF8_CSV)
    COURSE_GBK_CSV  = userInfo.get("COURSE_GBK_CSV", DEFAULT_COURSE_GBK_CSV)

    if coding == "utf-8":
        rows = read_csv(COURSE_UTF8_CSV, encoding="utf-8-sig")
    elif coding == "gbk":
        rows = read_csv(COURSE_GBK_CSV, encoding="gbk")
    else:
        raise NotImplementedError

    rows = [ { k:v.strip() for k,v in d.items() } for d in rows ] # 去除空格
    courses = []
    for d in rows:
        for k,v in d.items():
            if v.strip() == '': # 存在空格
                break
        else:
            courses.append(Course(**d))
    return courses
