#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: _compat.py

__all__ = [

    "json","JSONDecodeError",

    ]

try:
    import simplejson as json
    from simplejson.decoder import JSONDecodeError
except ImportError:
    import json
    from json.decoder import JSONDecodeError