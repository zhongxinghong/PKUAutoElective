#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: loop.py
# modified: 2019-09-09

__all__ = ["main"]

import sys
import time
import random
from collections import deque
from requests.compat import json
from requests.exceptions import RequestException
from . import __version__, __date__
from .iaaa import IAAAClient
from .elective import ElectiveClient
from .captcha import CaptchaRecognizer
from .course import Course
from .config import AutoElectiveConfig
from .parser import load_course_csv, get_tables, get_courses, get_courses_with_detail, get_sida
from .logger import ConsoleLogger, FileLogger
from .exceptions import *


iaaa = IAAAClient()
elective = ElectiveClient()
recognizer = CaptchaRecognizer()
config = AutoElectiveConfig()

cout = ConsoleLogger("loop")
ferr = FileLogger("loop.error") # loop 的子日志，同步输出到 console

interval = config.refreshInterval
deviation = config.refreshRandomDeviation
isDualDegree = config.isDualDegree
identity = config.identity

config.check_identify(identity)


def _get_refresh_interval():
    if deviation <= 0:
        return interval
    delta = (random.random() * 2 - 1) * deviation * interval
    return interval + delta


def _has_candidates(goals, ignored):
    _ignored = [ x[0] for x in ignored ]
    count = 0
    for course in goals:
        if course in _ignored:
            continue
        count += 1
    return count > 0


def _task_print_header():
    header = "# PKU Auto-Elective Tool v%s (%s) #" % (__version__, __date__)
    line = "#" + "-"*(len(header) - 2) + "#"
    cout.info(line)
    cout.info(header)
    cout.info(line)
    cout.info("")


def _task_print_goals(goals, ignored):
    """ 输出待选课程 """
    if not _has_candidates(goals, ignored):
        return
    line = "-" * 30
    cout.info("> Current tasks")
    cout.info(line)
    idx = 1
    _ignored = [ x[0] for x in ignored ]
    for course in goals:
        if course in _ignored:
            continue
        cout.info("%02d. %s" % (idx, course))
        idx += 1
    cout.info(line)
    cout.info("")


def _task_print_ignored(ignored):
    """ 输出忽略列表 """
    if len(ignored) == 0:
        return
    line = "-" * 30
    cout.info("> Ignored tasks")
    cout.info(line)
    idx = 1
    for course, reason in ignored:
        cout.info("%02d. %s  %s" % (idx, course, reason))
        idx += 1
    cout.info(line)
    cout.info("")


def _task_login():
    """ 登录 """
    cout.info("Try to login IAAA")
    iaaa.clear_cookies()
    elective.clear_cookies() # 清除旧的 cookies ，避免影响本次登录
    iaaa.oauth_login()
    resp = elective.sso_login(iaaa.token)
    if isDualDegree:
        sida = get_sida(resp)
        sttp = identity
        referer = resp.url
        elective.sso_login_dual_degree(sida, sttp, referer)
    cout.info("Login success")


def _task_get_available_courses(goals, plans, elected, ignored):
    queue = deque()
    _ignored = [ x[0] for x in ignored ]
    for c0 in goals:
        if c0 in _ignored:
            continue
        for c in elected:
            if c == c0:
                cout.info("%s is elected, ignored" % c0)
                ignored.append( (c0, "Elected") )
                break
        else:
            for c in plans:
                if c == c0:
                    if c.is_available():
                        queue.append(c)
                        cout.info("%s is AVAILABLE now !" % c)
                    break
            else:
                raise NotInCoursePlanException("%s is not in your course plan." % c0)
    return queue


def _task_validate_captcha():
    """ 填一次验证码 """
    while True:
        cout.info("Fetch a captcha")
        r = elective.get_DrawServlet()
        captcha = recognizer.recognize(r.content)
        code = captcha.code
        cout.info("Recognition result: %s" % code)

        r = elective.get_Validate(code)
        try:
            res = r.json()["valid"]  # 可能会返回一个错误网页 ...
        except Exception as e:
            ferr.error(e)
            cout.warning("Unable to validate captcha")
            raise OperationFailedError

        if res == "2":
            cout.info("Validation passed!")
            captcha.clear_cache()
            cout.info("Clear captcha cache")
            break
        elif res == "0":
            cout.info("Validation failed, try again")
        else:
            cout.warning("Unknown validation result: %s" % validRes)


def main(goals=None, ignored=None, status=None):

    loop = 0
    shouldQuitImmediately = False

    goals = load_course_csv() if goals is None else goals
    ignored = [] if ignored is None else ignored  # (course, reason)

    def _update_loop():
        if status is not None:
            status["loop"] = loop

    def _ignore_course(course, reason):
        ignored.append( (course.to_simplified(), reason) )


    _task_print_header()

    while True:

        if not _has_candidates(goals, ignored):
            cout.info("No tasks, exit")
            break

        loop += 1
        _update_loop()

        cout.info("======== Loop %d ========" % loop)
        cout.info("")


        # MARK: print current plans

        _task_print_goals(goals, ignored)
        _task_print_ignored(ignored)

        try:

            # MARK: login IAAA if needed

            if iaaa.isTokenExpired:
                _task_login()


            # MARK: check supply/cancel page

            cout.info("Get SupplyCancel page")
            '''while True:
                resp = elective.get_supplement() # 双学位第二页
                tables = get_tables(resp._tree)
                try:
                    elected = get_courses(tables[1])
                    plans = get_courses_with_detail(tables[0])
                except IndexError as e: # 遇到空页面返回。
                                        # 模拟方法：
                                        # 1.先登录辅双，打开补退选第二页
                                        # 2.再在同一浏览器登录主修
                                        # 3.刷新辅双的补退选第二页可以看到
                    cout.warning("IndexError encountered")
                    elective.get_SupplyCancel() # 需要先请求一次补退选主页（惰性）
                else:                           # 之后就可以不断刷新
                    break'''

            resp = elective.get_SupplyCancel()
            tables = get_tables(resp._tree)
            elected = get_courses(tables[1])
            plans = get_courses_with_detail(tables[0])


            # MARK: check available courses

            cout.info("Get available courses")
            queue = _task_get_available_courses(goals, plans, elected, ignored)


            # MAKR: elect available courses

            if len(queue) == 0:
                cout.info("No courses available")
                continue
            while len(queue) > 0:
                course = queue.popleft()
                cout.info("Try to elect %s" % course)

                _task_validate_captcha()

                retryRequired = True
                while retryRequired:
                    retryRequired = False
                    try:
                        resp = elective.get_ElectSupplement(course.href)

                    except (ElectionRepeatedError, TimeConflictError) as e:
                        ferr.error(e)
                        cout.warning("ElectionRepeatedError encountered")
                        _ignore_course(course, reason="Repeated")

                    except TimeConflictError as e:
                        ferr.error(e)
                        cout.warning("TimeConflictError encountered")
                        _ignore_course(course, reason="Time conflict")

                    except ExamTimeConflictError as e:
                        ferr.error(e)
                        cout.warning("ExamTimeConflictError encountered")
                        _ignore_course(course, reason="Exam time conflict")

                    except ElectionPermissionError as e:
                        ferr.error(e)
                        cout.warning("ElectionPermissionError encountered")
                        _ignore_course(course, reason="Permission required")

                    except CreditsLimitedError as e:
                        ferr.error(e)
                        cout.warning("CreditsLimitedError encountered")
                        _ignore_course(course, reason="Credits limited")

                    except MutuallyExclusiveCourseError as e:
                        ferr.error(e)
                        cout.warning("MutuallyExclusiveCourseError encountered")
                        _ignore_course(course, reason="Mutual exclusive")

                    except ElectionSuccess as e:
                        cout.info("%s is ELECTED !" % course) # 不从此处加入 ignored ，而是在下回合根据实际选课结果来决定是否忽略

                    except ElectionFailedError as e:
                        ferr.error(e)
                        cout.warning("ElectionFailedError encountered") # 具体原因不明，且不能马上重试
                        # cout.info("Retry to elect %s" % course)
                        # retryRequired = True

                    except Exception as e:
                        raise e

        except NotInCoursePlanException as e:
            cout.error(e)
            shouldQuitImmediately = True
            raise e

        except (ServerError, StatusCodeError) as e:
            ferr.error(e)
            cout.warning("ServerError/StatusCodeError encountered")

        except RequestException as e:
            ferr.error(e)
            cout.warning("RequestException encountered")

        except (SessionExpiredError, InvalidTokenError, NoAuthInfoError, SharedSessionError) as e:
            cout.error(e)
            iaaa.clear_token() # 删掉 token 下次循坏会重新登录
            cout.info("Need to login")
            iaaa.clear_cookies()     # 发生错误时很有可能是因为使用了过期 cookies ，由于 cookies 需要请求成功
            elective.clear_cookies() # 才能刷新，因此请求失败时必须强制清除，否则会导致死循环

        except CaughtCheatingError as e:
            ferr.critical(e) # 严重错误
            shouldQuitImmediately = True
            raise e

        except SystemException as e:
            ferr.error(e)
            cout.warning("SystemException encountered")

        except TipsException as e:
            ferr.error(e)
            cout.warning("TipsException encountered")

        except OperationTimeoutError as e:
            ferr.error(e)
            cout.warning("OperationTimeoutError encountered")

        except OperationFailedError as e:
            ferr.error(e)
            cout.warning("OperationFailedError encountered")

        except json.JSONDecodeError as e:
            ferr.error(e)
            cout.warning("JSONDecodeError encountered")

        except KeyboardInterrupt as e:
            shouldQuitImmediately = True
            raise e

        except Exception as e:
            ferr.exception(e)
            shouldQuitImmediately = True
            raise e

        finally:
            if shouldQuitImmediately:
                sys.exit(1)
            shouldQuitImmediately = False

            t = _get_refresh_interval()
            cout.info("")
            cout.info("======== END Loop %d ========" % loop)
            cout.info("Sleep %s s" % t)
            cout.info("")
            time.sleep(t)
