#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: monitor.py
# modified: 2019-09-11

__all__ = ["main"]

import logging
import werkzeug._internal as _werkzeug_internal
from flask import Flask, current_app, jsonify
from flask.logging import default_handler
from .config import AutoElectiveConfig
from .logger import ConsoleLogger


cout = ConsoleLogger("monitor")
ferr = ConsoleLogger("monitor.error")
config = AutoElectiveConfig()


def main(signals, goals, ignored, status):

    monitor = Flask(__name__)


    # MARK: register routes

    @monitor.route("/", methods=["GET"])
    @monitor.route("/rules", methods=["GET"])
    def root():
        rules = []
        for r in sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule):
            line = "{method}  {rule}".format(
                    method=','.join( m for m in r.methods if m not in ("HEAD","OPTIONS") ),
                    rule=r.rule
                )
            rules.append(line)
        return jsonify(rules)


    @monitor.route("/loop", methods=["GET"])
    def loop():
        return str(status["loop"])


    @monitor.route("/goals", methods=["GET"])
    def get_goals():
        return jsonify([ str(course) for course in goals ])


    @monitor.route("/current",methods=["GET"])
    def get_current():
        _ignored = [ x[0] for x in ignored ]
        return jsonify([ str(course) for course in goals if course not in _ignored ])


    @monitor.route("/ignored", methods=["GET"])
    def get_ignored():
        return jsonify([ "%s  %s" % (course, reason) for (course, reason) in ignored ])


    @monitor.route("/all", methods=["GET"])
    def get_all():
        _ignored = [ x[0] for x in ignored ]
        return jsonify(
            {
                "loop": status["loop"],
                "goals": [ str(course) for course in goals ],
                "current": [ str(course) for course in goals if course not in _ignored ],
                "ignored": [ "%s  %s" % (course, reason) for (course, reason) in ignored ],
            }
        )


    # MARK: setup monitor

    monitor.config["JSON_AS_ASCII"] = False
    monitor.config["JSON_SORT_KEYS"] = False


    _werkzeug_internal._logger = cout  # custom _logger for werkzeug

    monitor.logger.removeHandler(default_handler)
    for logger in [cout, ferr]:
        for handler in logger.handlers:
            monitor.logger.addHandler(handler)


    monitor.run(
        host=config.monitorHost,
        port=config.monitorPort,
        debug=True,
        use_reloader=False,
    )

