#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: recognizer.py
# modified: 2020-02-16

import os
import time
import numpy as np
import cv2
import torch
from .processor import split_captcha
from .cnn import CaptchaCNN


class Captcha(object):

    __slots__ = ['_code','_im_data','_im_segs']

    def __init__(self, code, im_data, im_segs):
        self._code = code
        self._im_data = im_data
        self._im_segs = im_segs

    @property
    def code(self):
        return self._code

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self._code,
        )

    def save(self, folder):
        code = self._code
        data = self._im_data
        segs = self._im_segs
        timestamp = int(time.time() * 1000)

        filepath = os.path.join(folder, "%s_%d.gif" % (code, timestamp))
        with open(filepath, 'wb') as fp:
            fp.write(data)

        for ix, M in enumerate(segs):
            filepath = os.path.join(folder, "%s_c%d_%d.png" % (code, ix, timestamp))
            cv2.imwrite(filepath, M)


class CaptchaRecognizer(object):

    def __init__(self, model_file):
        self._model = CaptchaCNN()
        self._model.load_state_dict(torch.load(model_file, map_location='cpu'))
        self._model.eval()

    def recognize(self, im_data):
        assert isinstance(im_data, bytes)

        N = 52
        labels = self._model.CAPTCHA_LABELS

        im_segs = split_captcha(im_data)
        Xlist = np.array(im_segs, dtype=np.float32).reshape(-1, 1, N, N)
        ylist = self._model(torch.from_numpy(Xlist))

        code = ''.join( labels[ix] for ix in torch.argmax(ylist, dim=1) )

        return Captcha(code, im_data, im_segs)
