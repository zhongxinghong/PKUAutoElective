#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: recognizer.py
# modified: 2020-02-16

import os
from io import BytesIO
import joblib
from PIL import Image
import numpy as np
import torch
from .processor import denoise8, denoise24, crop
from .cnn import CNN
from ..utils import xMD5
from ..const import CNN_MODEL_FILE


class Captcha(object):

    __slots__ = ['_code','_original','_denoised','_segments','_spans']

    def __init__(self, code, original, denoised, segments, spans):
        self._code = code
        self._original = original
        self._denoised = denoised
        self._segments = segments
        self._spans = spans

    @property
    def code(self):
        return self._code

    @property
    def original(self):
        return self._original

    @property
    def denoised(self):
        return self._denoised

    @property
    def segments(self):
        return self._segments

    @property
    def spans(self):
        return self._spans

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self._code,
        )

    def save(self, folder):
        code = self._code
        oim = self._original
        dim = self._denoised
        segs = self._segments
        spans = self._spans
        md5 = xMD5(oim.tobytes())

        oim.save(os.path.join(folder, "%s_original_%s.jpg" % (code, md5)))
        dim.save(os.path.join(folder, "%s_denoised_%s.jpg" % (code, md5)))
        for im, (st, ed), c in zip(segs, spans, code):
            im.save(os.path.join(folder, "%s_%s_(%d,%d)_%s.jpg" % (code, c, st, ed, md5)))


class CaptchaRecognizer(object):

    def __init__(self):
        self._model = CNN()
        self._model.load_state_dict(joblib.load(CNN_MODEL_FILE))

    def recognize(self, im):
        assert isinstance(im, bytes)

        N = 22

        fp = BytesIO(im)
        im = Image.open(fp)
        oim = im

        im = im.convert("1")

        im = denoise8(im, repeat=1)
        im = denoise24(im, repeat=1)
        dim = im

        segs, spans = crop(im)

        Xlist = []
        for im in segs:
            X = np.array(im, dtype=np.uint8)
            X = 1 - X
            Xlist.append(X)

        Xlist = np.array(Xlist, dtype=np.float32).reshape(-1, 1, N, N)
        ylist = self._model(torch.from_numpy(Xlist))

        code = ''.join( self._model.LABELS[ix] for ix in torch.argmax(ylist, dim=1) )

        return Captcha(code, oim, dim, segs, spans)
