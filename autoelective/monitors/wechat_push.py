#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: wechat_push.py
# modified: 2019-09-17

import requests, time, json
from threading import Timer
from ..environ import Environ
from ..config import AutoElectiveConfig
from ..logger import ConsoleLogger, FileLogger
from ..exceptions import UserInputException

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("wechatpush")
ferr = FileLogger("wechatpush.error")

elected_cache = [str(c) for c, r in environ.ignored.items() if r == 'Elected']
wechat_push_api = f'https://sc.ftqq.com/{config.monitor_wechatpush_key}.send'
# serverChan wechat pushservice api


def regular_report():
    # 定时报告
    it = environ.iaaa_loop_thread
    et = environ.elective_loop_thread
    it_alive = it is not None and it.is_alive()
    et_alive = et is not None and et.is_alive()
    finished = not it_alive and not et_alive
    error_encountered = not finished and (not it_alive or not et_alive)
    goals = environ.goals  # [course(name,class_no,school)]
    ignored = environ.ignored  # {course, reason}
    report_title = "选课助手运行报告"
    report_desp = f'''
## 选课统计  
- 目标: {str([str(c) for c in goals])}   
- 当前在选: {str([str(c) for c in goals if c not in ignored])}  
- 已选上: {str([str(c) for c, r in ignored.items() if r == "Elected"])}  
- 已忽略: {str({str(c): r for c, r in ignored.items()})}  
- 选课结束: {finished}  

## 运行情况统计  
- 统一身份认证循环次数: {environ.iaaa_loop}  
- 尝试选课循环次数: {environ.elective_loop}  
- 统一身份认证循环工作正常: {it_alive}  
- 尝试选课循环工作正常: {et_alive}  

## 错误统计  
- 错误计数: {error_encountered}  
- 错误描述: {environ.errors}  
    '''
    x = requests.post(wechat_push_api,
                      data={
                          "text": report_title,
                          "desp": report_desp
                      })
    error_code = int(json.loads(x.text)["errno"])
    error_msg = json.loads(x.text)["errmsg"]
    if error_code != 0:
        ferr.error(error_msg)
    else:
        cout.info("wechat regular push success")
    wechat_push_interval = config.monitor_wechatpush_pushinterval
    Timer(wechat_push_interval * 60, regular_report).start()


def report_elected(elected_courses):
    # 成功选课报告
    for elected_course in elected_courses:
        report_title = "{elected}已经选上".format(elected=elected_course)
        report_desp = f'''
## 恭喜！  
 
{elected_course}已经选上!  

点击[这里](https://elective.pku.edu.cn/)查看选课系统！  
        '''
        x = requests.post(wechat_push_api,
                          data={
                              "text": report_title,
                              "desp": report_desp
                          })
        error_code = int(json.loads(x.text)["errno"])
        error_msg = json.loads(x.text)["errmsg"]
        if error_code != 0:
            ferr.error(error_msg)
        else:
            cout.info("wechat elected course push success")


def run():
    # main loop of wechatpush service
    wechat_push_interval = config.monitor_wechatpush_pushinterval
    # 定时报告任务
    if isinstance(wechat_push_interval, int) and wechat_push_interval >= 10:
        cout.info("wechatpush regular report start!")
        regular_report()
    elif wechat_push_interval == 0:
        cout.info("no wechatpush regular report!")
    else:
        raise UserInputException("illegal wechat push interval!")
    while True:
        # 循环检测新选上的课
        global elected_cache
        tmp_elected = [
            str(c) for c, r in environ.ignored.items() if r == 'Elected'
        ]
        if tmp_elected != elected_cache:  # new elected courses
            report_elected(
                list(set(tmp_elected).difference(set(elected_cache))))
            elected_cache = tmp_elected
        time.sleep(1)
