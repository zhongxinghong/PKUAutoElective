from .environ import Environ
from .config import AutoElectiveConfig
from .logger import ConsoleLogger
import json
import requests
import re
import time

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("wechat_push")
ferr = ConsoleLogger("wechat_push.error")

sckey = config.wechat_push_sckey
enabled = environ.wechat_push

url = 'https://sc.ftqq.com/%s.send' % sckey

msg = """
# 选课助手运行报告
--------------------
## 选课状态
### 目标课程  
%s
### 当前进程  
%s
### 已忽略  
%s
--------------------
## 程序工作状态   
%s
%s
"""


def find_course(string):
    # 匹配解析课程
    p = re.compile(r'[(](.*)[)]', re.S)  # 贪婪匹配
    return re.findall(p, str(string))[0].split(',')


def message_formatter():
    # 格式化消息
    goal = ''
    currents = ''
    ignored = ''
    status = ''
    for c in environ.goals:
        goal += ('- ' + find_course(c)[0] + '  \n')
        if c not in environ.ignored:
            currents += ('- ' + find_course(c)[0] + '  \n')
    for c, r in environ.ignored.items():
        ignored += ('- ' + find_course(c)[0] + ':' + r + '  \n')
    it = environ.iaaa_loop_thread
    et = environ.elective_loop_thread
    it_alive = it is not None and it.is_alive()
    et_alive = et is not None and et.is_alive()
    finished = not it_alive and not et_alive
    error_encountered = not finished and (not it_alive or not et_alive)
    status += '- 身份认证循环数:' + str(environ.iaaa_loop) + '  \n'
    status += '- 选课循环次数:' + str(environ.elective_loop) + '  \n'
    status += '- 身份认证运行:' + str(it_alive) + '  \n'
    status += '- 选课运行:' + str(et_alive) + '  \n'
    status += '- 已结束:' + str(finished) + '  \n'
    status += '- 运行错误:' + str(error_encountered) + '  \n'
    error = ''
    if error_encountered is True:
        error = '--------------------\n## 错误报告  \n%s' % str(environ.errors)
    return msg % (goal, currents, ignored, status, error)


def log_push():
    # pushlog
    params = {"text": "选课助手运行报告", "desp": message_formatter()}
    return msg_push(params)


def success_push(course):
    # 选课成功
    if enabled:
        course = find_course(course)
        text = "%s已选上" % course[0]
        params = {"text": text, "desp": message_formatter()}
        return msg_push(params)


def available_push(course0):
    # 新课程可选
    if enabled:
        course = find_course(course0)
        text = "%s现在可选" % course[0]
        params = {"text": text, "desp": message_formatter()}
        return msg_push(params)


def msg_push(params):
    # 推送处理
    try:
        response = requests.get(url=url, params=params).text
        response = json.loads(response)
        if response['errno'] == 0:
            cout.info('wechat push success!')
        else:
            cout.error(response['errmsg'])
            ferr.error(response['errmsg'])
    except Exception as e:
        cout.error(e)
        ferr.error(e)


def run_wechat_push_watchdog():
    # log watchdog
    while True:
        log_push()
        time.sleep(3600)
