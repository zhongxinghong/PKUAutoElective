#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: main.py
# modified: 2019-09-11

from optparse import OptionParser
from threading import Thread
from multiprocessing import Queue
from autoelective import __version__, __date__
from autoelective.environ import Environ
from autoelective.config import AutoElectiveConfig

environ = Environ()
config = AutoElectiveConfig()


def main():

    parser = OptionParser(
        description='PKU Auto-Elective Tool v%s (%s)' %
        (__version__, __date__),
        version=__version__,
    )

    ## custom input files

    parser.add_option(
        '-c',
        '--config',
        dest='config_ini',
        metavar="FILE",
        help='custom config file encoded with utf8',
    )

    ## boolean (flag) options

    parser.add_option(
        '-m',
        '--with-monitor',
        dest='with_monitor',
        action='store_true',
        default=False,
        help='run the monitor thread simultaneously',
    )

    ## add wechat message push

    parser.add_option(
        '-w',
        '--wechat-push',
        dest='wechat_push',
        action='store_true',
        default=False,
        help='enable message push on WeChat',
    )

    options, args = parser.parse_args()

    environ.config_ini = options.config_ini
    environ.with_monitor = options.with_monitor
    environ.wechat_push = options.wechat_push

    # import here to ensure the singleton `config` will be init later than parse_args()
    from autoelective.loop import run_iaaa_loop, run_elective_loop
    from autoelective.monitor import run_monitor
    from autoelective.wechatpush import run_wechat_push_watchdog

    tList = []

    t = Thread(target=run_iaaa_loop, name="IAAA")
    environ.iaaa_loop_thread = t
    tList.append(t)

    t = Thread(target=run_elective_loop, name="Elective")
    environ.elective_loop_thread = t
    tList.append(t)

    if options.with_monitor:
        t = Thread(target=run_monitor, name="Monitor")
        environ.monitor_thread = t
        tList.append(t)

    if config.wechat_push_watchdog and options.wechat_push:
        t = Thread(target=run_wechat_push_watchdog, name="WechatPushWatchdog")
        environ.wechat_push_thread = t
        tList.append(t)

    for t in tList:
        t.daemon = True
        t.start()

    #
    # Don't use join() to block the main thread, or Ctrl + C in Windows can't work.
    #
    # for t in tList:
    #     t.join()
    #
    try:
        Queue().get()
    except KeyboardInterrupt as e:
        pass


if __name__ == '__main__':
    main()
