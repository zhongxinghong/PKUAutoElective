#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: test_cnn.py
# Created Date: 2021-03-10
# Author: Rabbit
# --------------------------------
# Copyright (c) 2021 Rabbit

import sys
sys.path.append("../")

import os
from autoelective.captcha import CaptchaRecognizer
from autoelective.const import CNN_MODEL_FILE

def test_captcha(r, code):
    filepath = os.path.join(os.path.dirname(__file__), './data/%s.gif' % code)

    with open(filepath, 'rb') as fp:
        im_data = fp.read()

    c = r.recognize(im_data)
    print(c, c.code == code)

def main():
    r = CaptchaRecognizer(CNN_MODEL_FILE)
    test_captcha(r, 'er47')
    test_captcha(r, 'rskh')
    test_captcha(r, 'uesg')
    test_captcha(r, 'skwc')
    test_captcha(r, 'mmfk')

if __name__ == "__main__":
    main()
