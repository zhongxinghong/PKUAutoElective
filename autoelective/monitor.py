#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: monitor.py
# modified: 2019-09-11

import logging
import werkzeug._internal as _werkzeug_internal
from flask import Flask, current_app, jsonify
from flask.logging import default_handler
from .environ import Environ
from .config import AutoElectiveConfig
from .logger import ConsoleLogger

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("monitor")
ferr = ConsoleLogger("monitor.error")

monitor = Flask(__name__, static_folder=None) # disable static rule

monitor.config["JSON_AS_ASCII"] = False
monitor.config["JSON_SORT_KEYS"] = False

_werkzeug_internal._logger = cout  # custom _logger for werkzeug

monitor.logger.removeHandler(default_handler)
for logger in [cout, ferr]:
    for handler in logger.handlers:
        monitor.logger.addHandler(handler)


@monitor.route("/", methods=["GET"])
@monitor.route("/rules", methods=["GET"])
@monitor.route("/stat", methods=["GET"], strict_slashes=False)
def _root():
    rules = []
    for r in sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule):
        line = "{method}  {rule}".format(
                method=','.join( m for m in r.methods if m not in ("HEAD","OPTIONS") ),
                rule=r.rule
            )
        rules.append(line)
    return jsonify({
        "rules": rules,
    })

@monitor.route("/stat/loop", methods=["GET"])
def _stat_iaaa_loop():
    it = environ.iaaa_loop_thread
    et = environ.elective_loop_thread
    it_alive = it is not None and it.is_alive()
    et_alive = et is not None and et.is_alive()
    finished = not it_alive and not et_alive
    error_encountered = not finished and ( not it_alive or not et_alive )
    return jsonify({
        "iaaa_loop": environ.iaaa_loop,
        "elective_loop": environ.elective_loop,
        "iaaa_loop_is_alive": it_alive,
        "elective_loop_is_alive": et_alive,
        "finished": finished,
        "error_encountered": error_encountered,
    })

@monitor.route("/stat/course", methods=["GET"])
def _stat_course():
    goals = environ.goals # [course]
    ignored = environ.ignored # {course, reason}
    return jsonify({
        "goals": [ str(c) for c in goals ],
        "current": [ str(c) for c in goals if c not in ignored ],
        "ignored": { str(c): r for c, r in ignored.items() },
    })

@monitor.route("/stat/error", methods=["GET"])
def _stat_error():
    return jsonify({
        "errors": environ.errors,
    })


def run_monitor():
    monitor.run(
        host=config.monitor_host,
        port=config.monitor_port,
        debug=True,
        use_reloader=False,
    )
