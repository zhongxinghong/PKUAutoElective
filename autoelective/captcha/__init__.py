#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: captcha/__init__.py

import os
from PIL import Image
from .preprocess import ImageProcessor
from .classifier import KNN, SVM, RandomForest
from ..const import Captcha_Cache_Dir
from ..util import Singleton, MD5, SHA1, ImmutableAttrsMixin

__all__ = ["CaptchaRecognizer",]


class CaptchaRecognitionResult(ImmutableAttrsMixin):

    def __init__(self, code, segs, spans, cache):
        self.code = code
        self.segs = tuple(segs)
        self.spans = tuple(spans)
        self.cache = tuple(cache)

    def clean_cache(self):
        for file in self.cache:
            if os.path.exists(file):
                os.remove(file)

    ### 可以选择退出时自动删除，也可以根据运行情况删除 ###
    '''def __del__(self):
        self.clear_cache()'''

    def __repr__(self):
        return '<%s: %r>' % (
                self.__class__.__name__,
                self.code,
            )

    def __eq__(self, other):
        return self.code == other



class CaptchaRecognizer(object, metaclass=Singleton):

    Classifier = SVM
    __HashFunc = MD5

    def __init__(self):
        self.clf = self.__class__.Classifier()

    @staticmethod
    def __abs_cp(path):
        return os.path.abspath(os.path.join(Captcha_Cache_Dir, path))

    def recognize(self, imgBytes):

        cache = []
        imgHash = self.__class__.__HashFunc(imgBytes)

        rawImgCacheFile = self.__abs_cp("%s.raw.jpg" % imgHash)
        with open(rawImgCacheFile, "wb") as fp:
            fp.write(imgBytes)
        cache.append(rawImgCacheFile)

        img = Image.open(rawImgCacheFile)
        img = img.convert("1")

        img = ImageProcessor.denoise8(img, repeat=1)
        img = ImageProcessor.denoise24(img, repeat=1)
        denoisedImgCacheFile = self.__abs_cp("%s.denoised.jpg" % imgHash)
        img.save(denoisedImgCacheFile)
        cache.append(denoisedImgCacheFile)

        segs, spans = ImageProcessor.crop(img)

        Xlist = [self.clf.feature(segImg) for segImg in segs]
        chars = self.clf.predict(Xlist)
        captcha = "".join(chars)

        for idx, (segImg, ch) in enumerate(zip(segs, chars)):
            segImgCacheFile = self.__abs_cp("%s.seg%d.%s.jpg" % (imgHash, idx, ch))
            segImg.save(segImgCacheFile)
            cache.append(segImgCacheFile)

        return CaptchaRecognitionResult(captcha, segs, spans, cache)
