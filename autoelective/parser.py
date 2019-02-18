#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: parser.py

from lxml import etree
from .course import Course
from .config import generalCfg
from .util import read_csv
from .const import Course_UTF8_CSV, Course_GBK_CSV
from .exceptions import UnsupportedCodingError

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
    return tree.find('.//head/title').text

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

def get_courses(table, fieldnames=["课程名","班号","开课单位"]):
    header = get_table_header(table)
    trs = get_table_trs(table)
    idxs = tuple(map(header.index, fieldnames))
    cs = []
    for tr in trs:
        t = tr.xpath('./th | ./td')
        name, classNo, school = map(lambda i: t[i].xpath('.//text()')[0], idxs)
        c = Course(name, classNo, school)
        cs.append(c)
    return cs

def get_courses_with_detail(table, fieldnames=["课程名","班号","开课单位","限数/已选","补选"]):
    header = get_table_header(table)
    trs = get_table_trs(table)
    idxs = tuple(map(header.index, fieldnames)) # 到时候要改
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
    coding = generalCfg.get("coding", "CSV_Coding")
    _coding = coding.lower()
    if _coding == "utf-8":
        file = Course_UTF8_CSV
        encoding = "utf-8-sig"
    elif _coding == "gbk":
        file = Course_GBK_CSV
        encoding = "gbk"
    else:
        raise UnsupportedCodingError(coding)

    rows = read_csv(file, encoding=encoding)
    rows = [{k:v.strip() for k,v in d.items()} for d in rows] # 去除空格
    courses = []
    for d in rows:
        for k,v in d.items():
            if v.strip() == "": # 存在空格
                break
        else:
            courses.append(Course(**d))
    return courses
