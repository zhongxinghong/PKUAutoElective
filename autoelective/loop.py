#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: loop.py
# modified: 2019-09-11

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
from .iaaa import IAAAClient
from .elective import ElectiveClient
from .const import CAPTCHA_CACHE_DIR
from .exceptions import *

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("loop")
ferr = FileLogger("loop.error") # loop 的子日志，同步输出到 console

username = config.iaaa_id
password = config.iaaa_password
is_dual_degree = config.is_dual_degree
identity = config.identity
interval = config.refresh_interval
deviation = config.refresh_random_deviation
page = config.supply_cancel_page
iaaa_timeout = config.iaaa_client_timeout
elective_timeout = config.elective_client_timeout
login_loop_interval = config.login_loop_interval
elective_pool_size = config.elective_client_pool_size

config.check_identify(identity)
config.check_supply_cancel_page(page)

recognizer = CaptchaRecognizer()

electivePool = Queue(maxsize=elective_pool_size)
reloginPool = Queue(maxsize=elective_pool_size)

goals = environ.goals
ignored = environ.ignored
mutexes = environ.mutexes

killedElective = ElectiveClient(-1)


class _ElectiveNeedsLogin(Exception):
    pass

def _get_refresh_interval():
    if deviation <= 0:
        return interval
    delta = (random.random() * 2 - 1) * deviation * interval
    return interval + delta

def _ignore_course(course, reason):
    ignored[course.to_simplified()] = reason

def _add_error(e):
    clz = e.__class__
    name = clz.__name__
    key = "[%s] %s" % (e.code, name) if hasattr(clz, "code") else name
    environ.errors[key] += 1


def run_iaaa_loop():

    elective = None

    while True:

        if elective is None:
            elective = reloginPool.get()
            if elective is killedElective:
                cout.info("Quit IAAA loop")
                return

        environ.iaaa_loop += 1

        cout.info("Try to login IAAA (client: %s)" % elective.id)

        try:

            iaaa = IAAAClient(timeout=iaaa_timeout) # not reusable

            r = iaaa.oauth_login(username, password)

            try:
                token = r.json()["token"]
            except Exception as e:
                ferr.error(e)
                raise OperationFailedError(msg="Unable to parse IAAA token. response body: %s" % r.content)

            elective.clear_cookies()
            r = elective.sso_login(token)

            if is_dual_degree:
                sida = get_sida(r)
                sttp = identity
                referer = r.url
                r = elective.sso_login_dual_degree(sida, sttp, referer)

            cout.info("Login success (client: %s)" % elective.id)

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

    ixd = {} # { cid: cix }

    for ix, (cid, c) in enumerate(cs.items()):
        goals.append(c)
        ixd[cid] = ix

    ## load mutex

    ms = config.mutexes

    N = len(cs)
    mutexes.resize((N, N), refcheck=False)

    for mid, cids in ms.items():
        ixs = []
        for cid in cids:
            if cid not in cs:
                raise UserInputException("In mutex:%s, course %r is not defined." % (mid, cid))
            ix = ixd[cid]
            ixs.append(ix)
        for ix1, ix2 in combinations(ixs, 2):
            mutexes[ix1, ix2] = mutexes[ix2, ix1] = 1

    ## setup elective pool

    for ix in range(1, elective_pool_size + 1):
        electivePool.put_nowait(ElectiveClient(id=ix, timeout=elective_timeout))

    ## print header

    header = "# PKU Auto-Elective Tool v%s (%s) #" % (__version__, __date__)
    line = "#" + "-" * (len(header) - 2) + "#"
    cout.info(line)
    cout.info(header)
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
            line = "-" * 30
            cout.info("> Current tasks")
            cout.info(line)
            for ix, course in enumerate(current):
                cout.info("%02d. %s" % (ix + 1, course))
            cout.info(line)
            cout.info("")

        ## print ignored course

        if len(ignored) > 0:
            line = "-" * 30
            cout.info("> Ignored tasks")
            cout.info(line)
            for ix, (course, reason) in enumerate(ignored.items()):
                cout.info("%02d. %s  %s" % (ix + 1, course, reason))
            cout.info(line)
            cout.info("")

        ## print mutex rules

        if mutexes.sum() > 0:
            line = "-" * 30
            cout.info("> Mutex rules")
            cout.info(line)
            ixs = [ (ix1, ix2) for ix1, ix2 in np.argwhere( mutexes == 1 ) if ix1 < ix2 ]
            for ix, (ix1, ix2) in enumerate(ixs):
                cout.info("%02d. %s --x-- %s" % (ix + 1, goals[ix1], goals[ix2]))
            cout.info(line)
            cout.info("")

        if len(current) == 0:
            cout.info("No tasks")
            cout.info("Quit elective loop")
            reloginPool.put_nowait(killedElective) # kill signal
            return

        ## print client info

        cout.info("> Current client: %s, (qsize: %s)" % (elective.id, electivePool.qsize() + 1))
        cout.info("")

        try:

            if not elective.hasLogined:
                raise _ElectiveNeedsLogin  # quit this loop

            ## check supply/cancel page

            if page == 1:

                cout.info("Get SupplyCancel page %s" % page)

                r = elective.get_SupplyCancel()
                tables = get_tables(r._tree)
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
                    r = elective.get_supplement(page=page) # 双学位第二页
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

            tasks = deque()
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
                        cout.info("%s is simultaneously ignored by user customed mutex rules" % mc)
                        _ignore_course(mc, "Mutex rules")
                else:
                    for c0 in plans: # c0 has detail
                        if c0 == c:
                            if c0.is_available():
                                tasks.append(c0)
                                cout.info("%s is AVAILABLE now !" % c0)
                            break
                    else:
                        raise UserInputException("%s is not in your course plan, please check your config." % c)

            ## elect available courses

            if len(tasks) == 0:
                cout.info("No course available")
                continue

            while len(tasks) > 0:

                course = tasks.popleft()
                cout.info("Try to elect %s" % course)

                ## validate captcha first

                while True:

                    cout.info("Fetch a captcha")
                    r = elective.get_DrawServlet()

                    captcha = recognizer.recognize(r.content)
                    cout.info("Recognition result: %s" % captcha.code)

                    r = elective.get_Validate(captcha.code)
                    try:
                        res = r.json()["valid"]  # 可能会返回一个错误网页 ...
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

                except MutuallyExclusiveCourseError as e:
                    ferr.error(e)
                    cout.warning("MutuallyExclusiveCourseError encountered")
                    _ignore_course(course, "Mutual exclusive")
                    _add_error(e)

                except MultiEnglishCourseError as e:
                    ferr.error(e)
                    cout.warning("MultiEnglishCourseError encountered")
                    _ignore_course(course, "Multi English course")
                    _add_error(e)

                except ElectionSuccess as e:
                    cout.info("%s is ELECTED !" % course)
                    # 不从此处加入 ignored ，而是在下回合根据教学网返回的实际选课结果来决定是否忽略

                except ElectionFailedError as e:
                    ferr.error(e)
                    cout.warning("ElectionFailedError encountered") # 具体原因不明，且不能马上重试
                    _add_error(e)

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
