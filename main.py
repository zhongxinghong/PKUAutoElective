#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: main.py

import time
import random
from collections import deque
from requests.exceptions import RequestException
from autoelective import __version__, __date__
from autoelective.iaaa import IAAAClient
from autoelective.elective import ElectiveClient
from autoelective.captcha import CaptchaRecognizer
from autoelective.course import Course
from autoelective.config import generalCfg
from autoelective.parser import load_course_csv, get_tables, get_courses, get_courses_with_detail, get_sida
from autoelective.logger import ConsoleLogger, FileLogger
from autoelective.exceptions import InvalidTokenError, InvalidSessionError, ServerError,\
    StatusCodeError, NotInCoursePlanException, SystemException, CaughtCheatingError,\
    ConflictingTimeError, RepeatedElectionError, OperationTimedOutError, ElectivePermissionError,\
    ElectionSuccess, ElectionFailedError, CreditLimitedError, MutuallyExclusiveCourseError,\
    NoAuthInfoError, SharedSessionError, UnsupportedIdentityError


iaaa = IAAAClient()
elective = ElectiveClient()
recognizer = CaptchaRecognizer()

cout = ConsoleLogger("main")
ferr = FileLogger("main.error") # main 的子日志，同步输出到 console

interval = generalCfg.getint("client", "Refresh_Interval")
deviation = generalCfg.getfloat("client", "Refresh_Interval_Random_Deviation")

isDualDegree = generalCfg.getboolean("user", "DualDegree")
if isDualDegree:
    identity = generalCfg.get("user", "Identity")
    if identity not in ("bzx", "bfx"):
        raise UnsupportedIdentityError("Identity must be in ('bzx','bfx')")


def get_refresh_interval():
    if deviation <= 0:
        return interval
    else:
        delta = (random.random() * 2 - 1) * deviation * interval
        return interval + delta

def has_candidates(goals, ignored):
    _ignored = [x[0] for x in ignored]
    count = 0
    for course in goals:
        if course in _ignored:
            continue
        count += 1
    return (count > 0)

def task_print_header():
    header = "# PKU Auto-Elective Tool v%s (%s) #" % (__version__, __date__)
    line = "#" + "-"*(len(header) - 2) + "#"
    cout.info(line)
    cout.info(header)
    cout.info(line)

def task_print_goals(goals, ignored):
    """ 输出待选课程 """
    if not has_candidates(goals, ignored):
        return
    cout.info("## Current candidates ##")
    cout.info("# ----------------------")
    _ignored = [x[0] for x in ignored]
    for course in goals:
        if course in _ignored:
            continue
        cout.info("# %s" % course)
    cout.info("# -------------------------")
    cout.info("# END Current candidates ##")

def task_print_ignored(ignored):
    """ 输出忽略列表 """
    if len(ignored) == 0:
        return
    cout.info("## Ignored courses ##")
    cout.info("# -------------------")
    for course, reason in ignored:
        cout.info("# %s %s" % (course, reason))
    cout.info("# -----------------------")
    cout.info("## END Ignored courses ##")

def task_login():
    """ 登录 """
    cout.info("Try to Login")
    iaaa.oauth_login()
    elective.clean_cookies() # 清除旧的 cookies ，避免影响本次登录
    resp = elective.sso_login(iaaa.token)
    if isDualDegree:
        sida = get_sida(resp)
        sttp = identity
        referer = resp.url
        elective.sso_login_dual_degree(sida, sttp, referer)
    cout.info("Login success !")

def task_get_available_courses(goals, plans, elected, ignored):
    queue = deque()
    _ignored = [x[0] for x in ignored]
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

def task_validate_captcha():
    """ 填一次验证码 """
    while True:
        cout.info("Get a captcha")
        resp = elective.get_DrawServlet()
        imgBytes = resp.content
        captcha = recognizer.recognize(imgBytes)
        code = captcha.code
        cout.info("Recognition Result: %s" % code)

        resp = elective.get_Validate(code)
        validRes = resp.json()["valid"]
        if validRes == "2":
            cout.info("Validation passed!")
            captcha.clean_cache()
            cout.info("Clear captcha cache")
            break
        elif validRes == "0":
            cout.info("Validation failed, try again")
        else:
            cout.warning("Unknown validation result: %s" % validRes)

def main():

    loop = 0
    loginRequired = True
    goals = load_course_csv()
    ignored = [] # (course, reason)

    task_print_header()

    while True:

        if not has_candidates(goals, ignored):
            cout.info("No candidates, exit")
            break

        loop += 1
        cout.info("Start loop %d" % loop)

        ## 输出当前计划 ##
        task_print_goals(goals, ignored)
        task_print_ignored(ignored)

        try:
            ## 登录 ##
            if loginRequired:
                task_login()
                loginRequired = False

            ## 获取补退选页信息 ##
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

            ## 获得可选课程 ##
            cout.info("Get available courses")
            queue = task_get_available_courses(goals, plans, elected, ignored)

            ## 依次选课 ##
            if len(queue) == 0:
                cout.info("No courses available")
                continue
            while len(queue) > 0:
                course = queue.popleft()
                cout.info("Try to elect %s" % course)

                task_validate_captcha()

                retryRequired = True
                while retryRequired:
                    retryRequired = False
                    try:
                        resp = elective.get_ElectSupplement(course.href)
                    except (RepeatedElectionError, ConflictingTimeError) as e:
                        ferr.error(e)
                        cout.warning("RepeatedElectionError encountered")
                        ignored.append( (course.to_simplified(), "Repeatd Election") )
                    except ConflictingTimeError as e:
                        ferr.error(e)
                        cout.warning("ConflictingTimeError encountered")
                        ignored.append( (course.to_simplified(), "Confliting Time") )
                    except ElectivePermissionError as e:
                        ferr.error(e)
                        cout.warning("ElectivePermissionError encountered")
                        ignored.append( (course.to_simplified(), "Electie Permission Required") )
                    except CreditLimitedError as e:
                        ferr.error(e)
                        cout.warning("CreditLimitedError encountered")
                        ignored.append( (course.to_simplified(), "CreditLimited") )
                    except MutuallyExclusiveCourseError as e:
                        ferr.error(e)
                        cout.warning("MutuallyExclusiveCourseError encountered")
                        ignored.append( (course.to_simplified(), "Mutex") )
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
            raise e
        except (ServerError, StatusCodeError) as e:
            ferr.error(e)
            cout.warning("ServerError/StatusCodeError encountered")
        except RequestException as e:
            ferr.error(e)
            cout.warning("RequestException encountered")
        except (InvalidSessionError, InvalidTokenError, NoAuthInfoError, SharedSessionError) as e:
            cout.error(e)
            loginRequired = True
            cout.info("Need to login")
            iaaa.clean_cookies()     # 发生错误时很有可能是因为使用了过期 cookies ，由于 cookies 需要请求成功
            elective.clean_cookies() # 才能刷新，因此请求失败时必须强制清除，否则会导致死循环
        except CaughtCheatingError as e:
            ferr.critical(e) # 严重错误
            raise e
        except SystemException as e:
            ferr.error(e)
            cout.warning("SystemException encountered")
        except OperationTimedOutError as e:
            ferr.error(e)
            cout.warning("OperationTimedOutError encountered")
        except Exception as e:
            ferr.exception(e)
            raise e
        finally:
            t = get_refresh_interval()
            cout.info("End loop %d, sleep %s s\n" % (loop, t))
            time.sleep(t)


if __name__ == '__main__':
    main()
