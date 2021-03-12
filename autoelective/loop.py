#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: loop.py
# modified: 2019-09-11

import os
import time
import random
from queue import Queue
from collections import deque
from itertools import combinations
from requests.compat import json
from requests.exceptions import RequestException
import numpy as np
from . import __version__, __date__
from .environ import Environ
from .config import AutoElectiveConfig
from .logger import ConsoleLogger, FileLogger
from .course import Course
from .captcha import CaptchaRecognizer
from .parser import get_tables, get_courses, get_courses_with_detail, get_sida
from .hook import _dump_request
from .iaaa import IAAAClient
from .elective import ElectiveClient
from .const import CAPTCHA_CACHE_DIR, USER_AGENT_LIST, WEB_LOG_DIR, CNN_MODEL_FILE
from .exceptions import *
from ._internal import mkdir

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("loop")
ferr = FileLogger("loop.error") # loop 的子日志，同步输出到 console

username = config.iaaa_id
password = config.iaaa_password
is_dual_degree = config.is_dual_degree
identity = config.identity
refresh_interval = config.refresh_interval
refresh_random_deviation = config.refresh_random_deviation
supply_cancel_page = config.supply_cancel_page
iaaa_client_timeout = config.iaaa_client_timeout
elective_client_timeout = config.elective_client_timeout
login_loop_interval = config.login_loop_interval
elective_client_pool_size = config.elective_client_pool_size
elective_client_max_life = config.elective_client_max_life
is_print_mutex_rules = config.is_print_mutex_rules

config.check_identify(identity)
config.check_supply_cancel_page(supply_cancel_page)

_USER_WEB_LOG_DIR = os.path.join(WEB_LOG_DIR, config.get_user_subpath())
mkdir(_USER_WEB_LOG_DIR)

recognizer = CaptchaRecognizer(CNN_MODEL_FILE)

electivePool = Queue(maxsize=elective_client_pool_size)
reloginPool = Queue(maxsize=elective_client_pool_size)

goals = environ.goals  # let N = len(goals);
ignored = environ.ignored
mutexes = np.zeros(0, dtype=np.uint8) # uint8 [N][N];
delays = np.zeros(0, dtype=np.int) # int [N];

killedElective = ElectiveClient(-1)
NO_DELAY = -1


class _ElectiveNeedsLogin(Exception):
    pass

class _ElectiveExpired(Exception):
    pass


def _get_refresh_interval():
    if refresh_random_deviation <= 0:
        return refresh_interval
    delta = (random.random() * 2 - 1) * refresh_random_deviation * refresh_interval
    return refresh_interval + delta

def _ignore_course(course, reason):
    ignored[course.to_simplified()] = reason

def _add_error(e):
    clz = e.__class__
    name = clz.__name__
    key = "[%s] %s" % (e.code, name) if hasattr(clz, "code") else name
    environ.errors[key] += 1

def _format_timestamp(timestamp):
    if timestamp == -1:
        return str(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def _dump_respose_content(content, filename):
    path = os.path.join(_USER_WEB_LOG_DIR, filename)
    with open(path, 'wb') as fp:
        fp.write(content)


def run_iaaa_loop():

    elective = None

    while True:

        if elective is None:
            elective = reloginPool.get()
            if elective is killedElective:
                cout.info("Quit IAAA loop")
                return

        environ.iaaa_loop += 1
        user_agent = random.choice(USER_AGENT_LIST)

        cout.info("Try to login IAAA (client: %s)" % elective.id)
        cout.info("User-Agent: %s" % user_agent)

        try:

            iaaa = IAAAClient(timeout=iaaa_client_timeout) # not reusable
            iaaa.set_user_agent(user_agent)

            # request elective's home page to get cookies
            r = iaaa.oauth_home()

            r = iaaa.oauth_login(username, password)

            try:
                token = r.json()["token"]
            except Exception as e:
                ferr.error(e)
                raise OperationFailedError(msg="Unable to parse IAAA token. response body: %s" % r.content)

            elective.clear_cookies()
            elective.set_user_agent(user_agent)

            r = elective.sso_login(token)

            if is_dual_degree:
                sida = get_sida(r)
                sttp = identity
                referer = r.url
                r = elective.sso_login_dual_degree(sida, sttp, referer)

            if elective_client_max_life == -1:
                elective.set_expired_time(-1)
            else:
                elective.set_expired_time(int(time.time()) + elective_client_max_life)

            cout.info("Login success (client: %s, expired_time: %s)" % (
                      elective.id, _format_timestamp(elective.expired_time)))
            cout.info("")

            electivePool.put_nowait(elective)
            elective = None

        except (ServerError, StatusCodeError) as e:
            ferr.error(e)
            cout.warning("ServerError/StatusCodeError encountered")
            _add_error(e)

        except OperationFailedError as e:
            ferr.error(e)
            cout.warning("OperationFailedError encountered")
            _add_error(e)

        except RequestException as e:
            ferr.error(e)
            cout.warning("RequestException encountered")
            _add_error(e)

        except IAAAIncorrectPasswordError as e:
            cout.error(e)
            _add_error(e)
            raise e

        except IAAAForbiddenError as e:
            ferr.error(e)
            _add_error(e)
            raise e

        except IAAAException as e:
            ferr.error(e)
            cout.warning("IAAAException encountered")
            _add_error(e)

        except CaughtCheatingError as e:
            ferr.critical(e) # 严重错误
            _add_error(e)
            raise e

        except ElectiveException as e:
            ferr.error(e)
            cout.warning("ElectiveException encountered")
            _add_error(e)

        except json.JSONDecodeError as e:
            ferr.error(e)
            cout.warning("JSONDecodeError encountered")
            _add_error(e)

        except KeyboardInterrupt as e:
            raise e

        except Exception as e:
            ferr.exception(e)
            _add_error(e)
            raise e

        finally:
            t = login_loop_interval
            cout.info("")
            cout.info("IAAA login loop sleep %s s" % t)
            cout.info("")
            time.sleep(t)


def run_elective_loop():

    elective = None
    noWait = False

    ## load courses

    cs = config.courses  # OrderedDict
    N = len(cs)
    cid_cix = {} # { cid: cix }

    for ix, (cid, c) in enumerate(cs.items()):
        goals.append(c)
        cid_cix[cid] = ix

    ## load mutex

    ms = config.mutexes
    mutexes.resize((N, N), refcheck=False)

    for mid, m in ms.items():
        ixs = []
        for cid in m.cids:
            if cid not in cs:
                raise UserInputException("In 'mutex:%s', course %r is not defined" % (mid, cid))
            ix = cid_cix[cid]
            ixs.append(ix)
        for ix1, ix2 in combinations(ixs, 2):
            mutexes[ix1, ix2] = mutexes[ix2, ix1] = 1

    ## load delay

    ds = config.delays
    delays.resize(N, refcheck=False)
    delays.fill(NO_DELAY)

    for did, d in ds.items():
        cid = d.cid
        if cid not in cs:
            raise UserInputException("In 'delay:%s', course %r is not defined" % (did, cid))
        ix = cid_cix[cid]
        delays[ix] = d.threshold

    ## setup elective pool

    for ix in range(1, elective_client_pool_size + 1):
        client = ElectiveClient(id=ix, timeout=elective_client_timeout)
        client.set_user_agent(random.choice(USER_AGENT_LIST))
        electivePool.put_nowait(client)

    ## print header

    header = "# PKU Auto-Elective Tool v%s (%s) #" % (__version__, __date__)
    line = "#" + "-" * (len(header) - 2) + "#"

    cout.info(line)
    cout.info(header)
    cout.info(line)
    cout.info("")

    line = "-" * 30

    cout.info("> User Agent")
    cout.info(line)
    cout.info("pool_size: %d" % len(USER_AGENT_LIST))
    cout.info(line)
    cout.info("")
    cout.info("> Config")
    cout.info(line)
    cout.info("is_dual_degree: %s" % is_dual_degree)
    cout.info("identity: %s" % identity)
    cout.info("refresh_interval: %s" % refresh_interval)
    cout.info("refresh_random_deviation: %s" % refresh_random_deviation)
    cout.info("supply_cancel_page: %s" % supply_cancel_page)
    cout.info("iaaa_client_timeout: %s" % iaaa_client_timeout)
    cout.info("elective_client_timeout: %s" % elective_client_timeout)
    cout.info("login_loop_interval: %s" % login_loop_interval)
    cout.info("elective_client_pool_size: %s" % elective_client_pool_size)
    cout.info("elective_client_max_life: %s" % elective_client_max_life)
    cout.info("is_print_mutex_rules: %s" % is_print_mutex_rules)
    cout.info(line)
    cout.info("")

    while True:

        noWait = False

        if elective is None:
            elective = electivePool.get()

        environ.elective_loop += 1

        cout.info("")
        cout.info("======== Loop %d ========" % environ.elective_loop)
        cout.info("")

        ## print current plans

        current = [ c for c in goals if c not in ignored ]
        if len(current) > 0:
            cout.info("> Current tasks")
            cout.info(line)
            for ix, course in enumerate(current):
                cout.info("%02d. %s" % (ix + 1, course))
            cout.info(line)
            cout.info("")

        ## print ignored course

        if len(ignored) > 0:
            cout.info("> Ignored tasks")
            cout.info(line)
            for ix, (course, reason) in enumerate(ignored.items()):
                cout.info("%02d. %s  %s" % (ix + 1, course, reason))
            cout.info(line)
            cout.info("")

        ## print mutex rules

        if np.any(mutexes):
            cout.info("> Mutex rules")
            cout.info(line)
            ixs = [ (ix1, ix2) for ix1, ix2 in np.argwhere( mutexes == 1 ) if ix1 < ix2 ]
            if is_print_mutex_rules:
                for ix, (ix1, ix2) in enumerate(ixs):
                    cout.info("%02d. %s --x-- %s" % (ix + 1, goals[ix1], goals[ix2]))
            else:
                cout.info("%d mutex rules" % len(ixs))
            cout.info(line)
            cout.info("")

        ## print delay rules

        if np.any( delays != NO_DELAY ):
            cout.info("> Delay rules")
            cout.info(line)
            ds = [ (cix, threshold) for cix, threshold in enumerate(delays) if threshold != NO_DELAY ]
            for ix, (cix, threshold) in enumerate(ds):
                cout.info("%02d. %s --- %d" % (ix + 1, goals[cix], threshold))
            cout.info(line)
            cout.info("")

        if len(current) == 0:
            cout.info("No tasks")
            cout.info("Quit elective loop")
            reloginPool.put_nowait(killedElective) # kill signal
            return

        ## print client info

        cout.info("> Current client: %s (qsize: %s)" % (elective.id, electivePool.qsize() + 1))
        cout.info("> Client expired time: %s" % _format_timestamp(elective.expired_time))
        cout.info("User-Agent: %s" % elective.user_agent)
        cout.info("")

        try:

            if not elective.has_logined:
                raise _ElectiveNeedsLogin  # quit this loop

            if elective.is_expired:
                try:
                    cout.info("Logout")
                    r = elective.logout()
                except Exception as e:
                    cout.warning("Logout error")
                    cout.exception(e)
                raise _ElectiveExpired   # quit this loop

            ## check supply/cancel page

            page_r = None

            if supply_cancel_page == 1:

                cout.info("Get SupplyCancel page %s" % supply_cancel_page)

                r = page_r = elective.get_SupplyCancel()
                tables = get_tables(r._tree)
                try:
                    elected = get_courses(tables[1])
                    plans = get_courses_with_detail(tables[0])
                except IndexError as e:
                    filename = "elective.get_SupplyCancel_%d.html" % int(time.time() * 1000)
                    _dump_respose_content(r.content, filename)
                    cout.info("Page dump to %s" % filename)
                    raise UnexceptedHTMLFormat

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
                        raise OperationFailedError(msg="unable to get normal Supplement page %s" % supply_cancel_page)

                    cout.info("Get Supplement page %s" % supply_cancel_page)
                    r = page_r = elective.get_supplement(page=supply_cancel_page) # 双学位第二页
                    tables = get_tables(r._tree)
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

            ## check available courses

            cout.info("Get available courses")

            tasks = [] # [(ix, course)]
            for ix, c in enumerate(goals):
                if c in ignored:
                    continue
                elif c in elected:
                    cout.info("%s is elected, ignored" % c)
                    _ignore_course(c, "Elected")
                    for (mix, ) in np.argwhere( mutexes[ix,:] == 1 ):
                        mc = goals[mix]
                        if mc in ignored:
                            continue
                        cout.info("%s is simultaneously ignored by mutex rules" % mc)
                        _ignore_course(mc, "Mutex rules")
                else:
                    for c0 in plans: # c0 has detail
                        if c0 == c:
                            if c0.is_available():
                                delay = delays[ix]
                                if delay != NO_DELAY and c0.remaining_quota > delay:
                                    cout.info("%s hasn't reached the delay threshold %d, skip" % (c0, delay))
                                else:
                                    tasks.append((ix, c0))
                                    cout.info("%s is AVAILABLE now !" % c0)
                            break
                    else:
                        raise UserInputException("%s is not in your course plan, please check your config." % c)

            tasks = deque([ (ix, c) for ix, c in tasks if c not in ignored ]) # filter again and change to deque

            ## elect available courses

            if len(tasks) == 0:
                cout.info("No course available")
                continue

            elected = []  # cache elected courses dynamically from `get_ElectSupplement`

            while len(tasks) > 0:

                ix, course = tasks.popleft()

                is_mutex = False

                # dynamically filter course by mutex rules
                for (mix, ) in np.argwhere( mutexes[ix,:] == 1 ):
                    mc = goals[mix]
                    if mc in elected: # ignore course in advanced
                        is_mutex = True
                        cout.info("%s --x-- %s" % (course, mc))
                        cout.info("%s is ignored by mutex rules in advance" % course)
                        _ignore_course(course, "Mutex rules")
                        break

                if is_mutex:
                    continue

                cout.info("Try to elect %s" % course)

                ## validate captcha first

                while True:

                    cout.info("Fetch a captcha")
                    r = elective.get_DrawServlet()

                    captcha = recognizer.recognize(r.content)
                    cout.info("Recognition result: %s" % captcha.code)

                    r = elective.get_Validate(username, captcha.code)
                    try:
                        res = r.json()["valid"]  # 可能会返回一个错误网页
                    except Exception as e:
                        ferr.error(e)
                        raise OperationFailedError(msg="Unable to validate captcha")

                    if res == "2":
                        cout.info("Validation passed")
                        break
                    elif res == "0":
                        cout.info("Validation failed")
                        captcha.save(CAPTCHA_CACHE_DIR)
                        cout.info("Save %s to %s" % (captcha, CAPTCHA_CACHE_DIR))
                        cout.info("Try again")
                    else:
                        cout.warning("Unknown validation result: %s" % res)

                ## try to elect

                try:

                    r = elective.get_ElectSupplement(course.href)

                except ElectionRepeatedError as e:
                    ferr.error(e)
                    cout.warning("ElectionRepeatedError encountered")
                    _ignore_course(course, "Repeated")
                    _add_error(e)

                except TimeConflictError as e:
                    ferr.error(e)
                    cout.warning("TimeConflictError encountered")
                    _ignore_course(course, "Time conflict")
                    _add_error(e)

                except ExamTimeConflictError as e:
                    ferr.error(e)
                    cout.warning("ExamTimeConflictError encountered")
                    _ignore_course(course, "Exam time conflict")
                    _add_error(e)

                except ElectionPermissionError as e:
                    ferr.error(e)
                    cout.warning("ElectionPermissionError encountered")
                    _ignore_course(course, "Permission required")
                    _add_error(e)

                except CreditsLimitedError as e:
                    ferr.error(e)
                    cout.warning("CreditsLimitedError encountered")
                    _ignore_course(course, "Credits limited")
                    _add_error(e)

                except MutexCourseError as e:
                    ferr.error(e)
                    cout.warning("MutexCourseError encountered")
                    _ignore_course(course, "Mutual exclusive")
                    _add_error(e)

                except MultiEnglishCourseError as e:
                    ferr.error(e)
                    cout.warning("MultiEnglishCourseError encountered")
                    _ignore_course(course, "Multi English course")
                    _add_error(e)

                except MultiPECourseError as e:
                    ferr.error(e)
                    cout.warning("MultiPECourseError encountered")
                    _ignore_course(course, "Multi PE course")
                    _add_error(e)

                except ElectionFailedError as e:
                    ferr.error(e)
                    cout.warning("ElectionFailedError encountered") # 具体原因不明，且不能马上重试
                    _add_error(e)

                except QuotaLimitedError as e:
                    ferr.error(e)
                    # 选课网可能会发回异常数据，本身名额 180/180 的课会发 180/0，这个时候选课会得到这个错误
                    if course.used_quota == 0:
                        cout.warning("Abnormal status of %s, a bug of 'elective.pku.edu.cn' found" % course)
                    else:
                        ferr.critical("Unexcepted behaviour") # 没有理由运行到这里
                        _add_error(e)

                except ElectionSuccess as e:
                    # 不从此处加入 ignored，而是在下回合根据教学网返回的实际选课结果来决定是否忽略
                    cout.info("%s is ELECTED !" % course)

                    # --------------------------------------------------------------------------
                    # Issue #25
                    # --------------------------------------------------------------------------
                    # 但是动态地更新 elected，如果同一回合内有多门课可以被选，并且根据 mutex rules，
                    # 低优先级的课和刚选上的高优先级课冲突，那么轮到低优先级的课提交选课请求的时候，
                    # 根据这个动态更新的 elected 它将会被提前地忽略（而不是留到下一循环回合的开始时才被忽略）
                    # --------------------------------------------------------------------------
                    r = e.response  # get response from error ... a bit ugly
                    tables = get_tables(r._tree)
                    # use clear() + extend() instead of op `=` to ensure `id(elected)` doesn't change
                    elected.clear()
                    elected.extend(get_courses(tables[1]))

                except RuntimeError as e:
                    ferr.critical(e)
                    ferr.critical("RuntimeError with Course(name=%r, class_no=%d, school=%r, status=%s, href=%r)" % (
                                    course.name, course.class_no, course.school, course.status, course.href))
                    # use this private function of 'hook.py' to dump the response from `get_SupplyCancel` or `get_supplement`
                    file = _dump_request(page_r)
                    ferr.critical("Dump response from 'get_SupplyCancel / get_supplement' to %s" % file)
                    raise e

                except Exception as e:
                    raise e  # don't increase error count here

        except UserInputException as e:
            cout.error(e)
            _add_error(e)
            raise e

        except (ServerError, StatusCodeError) as e:
            ferr.error(e)
            cout.warning("ServerError/StatusCodeError encountered")
            _add_error(e)

        except OperationFailedError as e:
            ferr.error(e)
            cout.warning("OperationFailedError encountered")
            _add_error(e)

        except UnexceptedHTMLFormat as e:
            ferr.error(e)
            cout.warning("UnexceptedHTMLFormat encountered")
            _add_error(e)

        except RequestException as e:
            ferr.error(e)
            cout.warning("RequestException encountered")
            _add_error(e)

        except IAAAException as e:
            ferr.error(e)
            cout.warning("IAAAException encountered")
            _add_error(e)

        except _ElectiveNeedsLogin as e:
            cout.info("client: %s needs Login" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            noWait = True

        except _ElectiveExpired as e:
            cout.info("client: %s expired" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            noWait = True

        except (SessionExpiredError, InvalidTokenError, NoAuthInfoError, SharedSessionError) as e:
            ferr.error(e)
            _add_error(e)
            cout.info("client: %s needs relogin" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            noWait = True

        except CaughtCheatingError as e:
            ferr.critical(e) # critical error !
            _add_error(e)
            raise e

        except SystemException as e:
            ferr.error(e)
            cout.warning("SystemException encountered")
            _add_error(e)

        except TipsException as e:
            ferr.error(e)
            cout.warning("TipsException encountered")
            _add_error(e)

        except OperationTimeoutError as e:
            ferr.error(e)
            cout.warning("OperationTimeoutError encountered")
            _add_error(e)

        except json.JSONDecodeError as e:
            ferr.error(e)
            cout.warning("JSONDecodeError encountered")
            _add_error(e)

        except KeyboardInterrupt as e:
            raise e

        except Exception as e:
            ferr.exception(e)
            _add_error(e)
            raise e

        finally:

            if elective is not None: # change elective client
                electivePool.put_nowait(elective)
                elective = None

            if noWait:
                cout.info("")
                cout.info("======== END Loop %d ========" % environ.elective_loop)
                cout.info("")
            else:
                t = _get_refresh_interval()
                cout.info("")
                cout.info("======== END Loop %d ========" % environ.elective_loop)
                cout.info("Main loop sleep %s s" % t)
                cout.info("")
                time.sleep(t)
