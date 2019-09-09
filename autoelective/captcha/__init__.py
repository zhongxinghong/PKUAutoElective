#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: __init__.py
# modified: 2019-09-08

__all__ = ["CaptchaRecognizer"]

import os
from PIL import Image
from .processor import denoise8, denoise24, crop
from .classifier import KNN, SVM, RandomForest
from ..const import CAPTCHA_CACHE_DIR
from ..utils import Singleton, xMD5, xSHA1


def _captcha_cache_file(*paths):
    return os.path.abspath(os.path.join(CAPTCHA_CACHE_DIR, *paths))


class CaptchaRecognitionResult(object):

    def __init__(self, code, segs, spans, cache):
        self.code = code
        self.segs = segs
        self.spans = spans
        self.cache = cache

    def __repr__(self):
        return '<%s: %r>' % (
                self.__class__.__name__,
                self.code,
            )

    def clear_cache(self):
        for file in self.cache:
            if os.path.exists(file):
                os.remove(file)


class CaptchaRecognizer(object, metaclass=Singleton):

    def __init__(self):
        self._clf = SVM()

    def recognize(self, imgBytes):

        cache = []
        imgHash = xMD5(imgBytes)

        rawImgCacheFile = _captcha_cache_file("%s.raw.jpg" % imgHash)
        with open(rawImgCacheFile, "wb") as fp:
            fp.write(imgBytes)

        cache.append(rawImgCacheFile)

        img = Image.open(rawImgCacheFile)
        img = img.convert("1")

        img = denoise8(img, repeat=1)
        img = denoise24(img, repeat=1)
        denoisedImgCacheFile = _captcha_cache_file("%s.denoised.jpg" % imgHash)
        img.save(denoisedImgCacheFile)
        cache.append(denoisedImgCacheFile)

        segs, spans = crop(img)

        Xlist = [ self._clf.feature(segImg) for segImg in segs ]
        chars = self._clf.predict(Xlist)
        captcha = "".join(chars)

        for idx, (segImg, ch) in enumerate(zip(segs, chars)):
            segImgCacheFile = _captcha_cache_file("%s.seg%d.%s.jpg" % (imgHash, idx, ch))
            segImg.save(segImgCacheFile)
            cache.append(segImgCacheFile)

        return CaptchaRecognitionResult(captcha, segs, spans, cache)
