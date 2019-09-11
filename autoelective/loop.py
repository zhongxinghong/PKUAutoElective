#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: loop.py
# modified: 2019-09-11

__all__ = ["main"]

import time
import random
from queue import Queue, Empty
from collections import deque
from threading import Thread, current_thread
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
from .const import SIGNAL_KILL_ALL_PROCESSES
from .exceptions import *


cout = ConsoleLogger("loop")
ferr = FileLogger("loop.error") # loop 的子日志，同步输出到 console

config = AutoElectiveConfig()

interval = config.refreshInterval
deviation = config.refreshRandomDeviation
isDualDegree = config.isDualDegree
identity = config.identity
page = config.supplyCancelPage
loginLoopInterval = config.loginLoopInterval
electivePoolSize = config.electiveClientPoolSize

config.check_identify(identity)
config.check_supply_cancel_page(page)

recognizer = CaptchaRecognizer()
electivePool = Queue(maxsize=electivePoolSize)
reloginPool = Queue(maxsize=electivePoolSize)

shouldKillAllThreads = False


class _ElectiveNeedsLogin(Exception):
    pass


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


def _get_available_courses(goals, plans, elected, ignored):
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


def _task_setup_pools():
    for i in range(1, electivePoolSize+1):
        electivePool.put_nowait(ElectiveClient(id=i))


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


def _task_validate_captcha(elective):
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
            raise OperationFailedError(msg="Unable to validate captcha")

        if res == "2":
            cout.info("Validation passed!")
            captcha.clear_cache()
            cout.info("Clear captcha cache")
            break
        elif res == "0":
            cout.info("Validation failed, try again")
        else:
            cout.warning("Unknown validation result: %s" % validRes)


def _task_print_current_thread_killed():
    cout.info("Kill thread %s" % current_thread().name)


def _task_send_signal_to_kill_all_blocking_threads():
    if electivePool.empty():
        electivePool.put_nowait(None)
    if reloginPool.empty():
        reloginPool.put_nowait(None)


def _thread_login_loop(status):

    elective = None

    shouldQuitImmediately = False
    global shouldKillAllThreads

    while True:

        shouldQuitImmediately = False

        if shouldKillAllThreads: # a signal to kill this thread
            _task_print_current_thread_killed()
            return

        if elective is None:
            elective = reloginPool.get()
            if elective is None: # a signal to kill this thread
                _task_print_current_thread_killed()
                return

        try:
            cout.info("Try to login IAAA (client: %s)" % elective.id)

            iaaa = IAAAClient() # not reusable

            r = iaaa.oauth_login()
            try:
                token = r.json()["token"]
            except Exception as e:
                ferr.error(e)
                raise OperationFailedError(msg="Unable to parse IAAA token. response body: %s" % r.content)

            elective.clear_cookies()
            r = elective.sso_login(token)

            if isDualDegree:
                sida = get_sida(r)
                sttp = identity
                referer = r.url
                _ = elective.sso_login_dual_degree(sida, sttp, referer)

            cout.info("Login success (client: %s)" % elective.id)

            electivePool.put_nowait(elective)
            elective = None

        except (ServerError, StatusCodeError) as e:
            ferr.error(e)
            cout.warning("ServerError/StatusCodeError encountered")

        except OperationFailedError as e:
            ferr.error(e)
            cout.warning("OperationFailedError encountered")

        except RequestException as e:
            ferr.error(e)
            cout.warning("RequestException encountered")

        except IAAAIncorrectPasswordError as e:
            cout.error(e)
            shouldQuitImmediately = True
            raise e

        except IAAAForbiddenError as e:
            ferr.error(e)
            shouldQuitImmediately = True
            raise e

        except IAAAException as e:
            ferr.error(e)
            cout.warning("IAAAException encountered")

        except CaughtCheatingError as e:
            ferr.critical(e) # 严重错误
            shouldQuitImmediately = True
            raise e

        except ElectiveException as e:
            ferr.error(e)
            cout.warning("ElectiveException encountered")

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
                shouldKillAllThreads = True
                _task_print_current_thread_killed()
                _task_send_signal_to_kill_all_blocking_threads()
                return

            t = loginLoopInterval
            cout.info("")
            cout.info("IAAA login loop sleep %s s" % t)
            cout.info("")
            time.sleep(t)


def _thread_main_loop(goals, ignored, status):

    loop = 0
    elective = None

    shouldQuitImmediately = False
    shouldEnterNextLoopImmediately = False
    global shouldKillAllThreads

    def _update_loop():
        if status is not None:
            status["loop"] = loop

    def _ignore_course(course, reason):
        ignored.append( (course.to_simplified(), reason) )


    _task_setup_pools()
    _task_print_header()


    while True:

        shouldQuitImmediately = False
        shouldEnterNextLoopImmediately = False

        if shouldKillAllThreads: # a signal to kill this thread
            _task_print_current_thread_killed()
            return

        if not _has_candidates(goals, ignored):
            cout.info("No tasks, exit")
            _task_print_current_thread_killed()
            _task_send_signal_to_kill_all_blocking_threads()
            return

        loop += 1
        _update_loop()

        cout.info("")
        cout.info("======== Loop %d ========" % loop)
        cout.info("")

        # MARK: print current plans

        _task_print_goals(goals, ignored)
        _task_print_ignored(ignored)

        try:
            if elective is None:
                elective = electivePool.get()
                if elective is None: # a signal to kill this thread
                    shouldQuitImmediately = True
                    return # log will be print in `finally` block

            cout.info("> Current client: %s, (qsize: %s)" % (elective.id, electivePool.qsize() + 1))
            cout.info("")

            if not elective.hasLogined:
                raise _ElectiveNeedsLogin  # quit this loop

            # MARK: check supply/cancel page

            if page == 1:

                cout.info("Get SupplyCancel page %s" % page)

                resp = elective.get_SupplyCancel()
                tables = get_tables(resp._tree)
                elected = get_courses(tables[1])
                plans = get_courses_with_detail(tables[0])

            else:
                #
                # 刷新非第一页的课程，第一次请求会遇到返回空页面的情况
                #
                # 模拟方法：
                # 1.先登录辅双，打开补退选第二页
                # 2.再在同一浏览器登录主修
                # 3.刷新辅双的补退选第二页可以看到
                #
                # -----------------------------------------------
                #
                # 引入 retry 逻辑以防止以为某些特殊原因无限重试
                # 正常情况下一次就能成功，但是为了应对某些偶发错误，这里设为最多尝试 3 次
                #
                retry = 3
                while True:
                    if retry == 0:
                        raise OperationFailedError(msg="unable to get normal Supplement page %s" % page)

                    cout.info("Get Supplement page %s" % page)
                    resp = elective.get_supplement(page=page) # 双学位第二页
                    tables = get_tables(resp._tree)
                    try:
                        elected = get_courses(tables[1])
                        plans = get_courses_with_detail(tables[0])
                    except IndexError as e:
                        cout.warning("IndexError encountered")
                        cout.info("Get SupplyCancel first to prevent empty table returned")
                        _ = elective.get_SupplyCancel() # 遇到空页面时请求一次补退选主页，之后就可以不断刷新
                    else:
                        break
                    finally:
                        retry -= 1


            # MARK: check available courses

            cout.info("Get available courses")
            queue = _get_available_courses(goals, plans, elected, ignored)


            # MAKR: elect available courses

            if len(queue) == 0:
                cout.info("No courses available")
                continue
            while len(queue) > 0:
                course = queue.popleft()
                cout.info("Try to elect %s" % course)

                _task_validate_captcha(elective)

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

                    except Exception as e:
                        raise e

        except NotInCoursePlanException as e:
            cout.error(e)
            shouldQuitImmediately = True
            raise e

        except (ServerError, StatusCodeError) as e:
            ferr.error(e)
            cout.warning("ServerError/StatusCodeError encountered")

        except OperationFailedError as e:
            ferr.error(e)
            cout.warning("OperationFailedError encountered")

        except RequestException as e:
            ferr.error(e)
            cout.warning("RequestException encountered")

        except IAAAException as e:
            ferr.error(e)
            cout.warning("IAAAException encountered")

        except _ElectiveNeedsLogin as e:
            cout.info("client: %s needs Login" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            shouldEnterNextLoopImmediately = True

        except (SessionExpiredError, InvalidTokenError, NoAuthInfoError, SharedSessionError) as e:
            ferr.error(e)
            cout.info("client: %s needs relogin" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            shouldEnterNextLoopImmediately = True

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
                shouldKillAllThreads = True
                _task_print_current_thread_killed()
                _task_send_signal_to_kill_all_blocking_threads()
                return

            if elective is not None: # change elective client
                electivePool.put_nowait(elective)
                elective = None

            if shouldEnterNextLoopImmediately:
                cout.info("")
                cout.info("======== END Loop %d ========" % loop)
                cout.info("")
            else:
                t = _get_refresh_interval()
                cout.info("")
                cout.info("======== END Loop %d ========" % loop)
                cout.info("Main loop sleep %s s" % t)
                cout.info("")
                time.sleep(t)


def main(signals=None, goals=None, ignored=None, status=None):

    goals = load_course_csv() if goals is None else goals
    ignored = [] if ignored is None else ignored  # (course, reason)

    tList = [
        Thread(target=_thread_login_loop, name="Loop-Login", args=(status,)),
        Thread(target=_thread_main_loop, name="Loop-Main", args=(goals, ignored, status))
    ]

    for t in tList:
        t.daemon = True
        t.start()

    try:
        for t in tList:
            t.join()
    except Exception as e:
        raise e
    finally:
        if signals is not None:
            signals.put_nowait(SIGNAL_KILL_ALL_PROCESSES)
