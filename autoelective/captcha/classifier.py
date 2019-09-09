#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: classifier.py
# modified: 2019-09-08

__all__ = ["KNN","SVM","RandomForest"]

import os
import re
from sklearn.neighbors.classification import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble.forest import RandomForestClassifier
from sklearn.externals import joblib
from .feature import get_feature_extractor
from ..const import MODEL_DIR
from ..utils import Singleton


_regexModelFilename = re.compile(
    pattern=(
        r'^(?P<alg>\S+)\.model\.'
        r'f(?P<feature>[1-5])\.'
        r'(?:l(?P<level>\d{1})\.)*'
        r'c(?P<compress>\d{1})'
        r'(?P<ext>\.z|\.gz|\.bz2|\.xz|\.lzma)$'
    ),
    flags=re.I,
)

def _get_MODEL_FILES():

    model_files = {}
    for file in os.listdir(MODEL_DIR):
        res = _regexModelFilename.match(file)
        if res is not None:
            filename = res.group()
            resDict = res.groupdict()
            alg = resDict.pop("alg")
            resDict["path"] = os.path.abspath(os.path.join(MODEL_DIR, filename))
            model_files[alg] = resDict

    return model_files


_MODEL_FILES = _get_MODEL_FILES()


class BaseClassifier(object, metaclass=Singleton):

    ALG = ""

    def __init__(self):
        if self.__class__ is __class__:
            raise NotImplementedError
        clf, feature = self._load_model()
        self._clf = clf
        self.feature = feature

    def _load_model(self):
        alg = self.__class__.ALG
        detail = _MODEL_FILES.get(alg)
        path, fCode, lCode = map(detail.__getitem__, ("path","feature","level"))
        feature = get_feature_extractor(fCode, lCode)
        if path is None:
            raise FileNotFoundError("model %s.* is missing" % alg)
        return joblib.load(path), feature

    def predict(self, Xlist):
        return self._clf.predict(Xlist)


class RandomForest(BaseClassifier):

    ALG = "RandomForest"


class KNN(BaseClassifier):

    ALG = "KNN"


class SVM(BaseClassifier):

    ALG = "SVM"