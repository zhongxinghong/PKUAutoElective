#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: main.py
# modified: 2019-09-11

import time
from optparse import OptionParser
from multiprocessing import Process, Manager, Queue
from autoelective import __version__, __date__


def task_run_loop():

    from autoelective.loop import main as run_main_loop
    run_main_loop()


def task_run_loop_with_monitor():

    from autoelective.parser import load_course_csv
    from autoelective.loop import main as run_main_loop
    from autoelective.monitor import main as run_monitor
    from autoelective.logger import ConsoleLogger
    from autoelective.const import SIGNAL_KILL_ALL_PROCESSES
    from autoelective.compat import install_ctrl_c_handler

    cout = ConsoleLogger("main")
    signals = Queue()

    with Manager() as manager:

        # shared objects
        goals = manager.list(load_course_csv())
        ignored = manager.list()
        status = manager.dict()

        status["loop"] = 0

        pList = [
            Process(target=run_main_loop, args=(signals, goals, ignored, status), name="Loop"),
            Process(target=run_monitor, args=(signals, goals, ignored, status), name="Monitor"),
        ]

        for p in pList:
            p.daemon = True
            p.start()

        install_ctrl_c_handler()

        while True:
            signal = signals.get()
            time.sleep(0.1) # Wait a minute
            if signal == SIGNAL_KILL_ALL_PROCESSES:
                for p in pList:
                    if p.is_alive():
                        p.terminate()
                    cout.info("Process %s is killed" % p.name)
                break

def main():

    parser = OptionParser(
        description='PKU Auto-Elective Tool v%s (%s)' % (__version__, __date__),
        version=__version__,
    )

    # MARK: custom input files

    parser.add_option(
        '--config',
        dest='CONFIG_INI',
        metavar="FILE",
        help='custom config file encoded with utf8',
    )
    parser.add_option(
        '--course-csv-utf8',
        dest='COURSE_UTF8_CSV',
        metavar="FILE",
        help='custom course.csv file encoded with utf8',
    )
    parser.add_option(
        '--course-csv-gbk',
        dest='COURSE_GBK_CSV',
        metavar="FILE",
        help='custom course.csv file encoded with gbk',
    )

    # MARK: boolean (flag) options

    parser.add_option(
        '--with-monitor',
        dest='with_monitor',
        action='store_true',
        default=False,
        help='run the monitor process simultaneously',
    )


    options, args = parser.parse_args()
    run_task = task_run_loop

    # MARK: setup custom const

    import autoelective.const as const

    if options.CONFIG_INI is not None:
        const.CONFIG_INI = options.CONFIG_INI

    if options.COURSE_UTF8_CSV is not None:
        const.COURSE_UTF8_CSV = options.COURSE_UTF8_CSV

    if options.COURSE_GBK_CSV is not None:
        const.COURSE_GBK_CSV = options.COURSE_GBK_CSV

    # MAKR: handle boolean (flag) options

    if options.with_monitor:
        run_task = task_run_loop_with_monitor


    run_task()


if __name__ == '__main__':
    main()
