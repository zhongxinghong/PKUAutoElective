#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: captcha/classifier.py

import os
import re
from sklearn.neighbors.classification import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble.forest import RandomForestClassifier
from sklearn.externals import joblib
from .feature import FeatureExtractor
from ..const import Model_Dir
from ..util import Singleton
from ..exceptions import ModelFileNotFoundError, ABCNotImplementedError

__all__ = ["KNN","SVM","RandomForest",]


def __get_Model_Files():

    regex_model_filename = re.compile(\
        r"^(?P<alg>\S+)\.model\."   + \
        r"f(?P<feature>[1-5])\."    + \
        r"(?:l(?P<level>\d{1})\.)*" + \
        r"c(?P<compress>\d{1})"     + \
        r"(?P<ext>\.z|\.gz|\.bz2|\.xz|\.lzma)$", re.I)

    model_files = {}
    for file in os.listdir(Model_Dir):
        res = regex_model_filename.match(file)
        if res is not None:
            filename = res.group()
            resDict = res.groupdict()
            alg = resDict.pop("alg")
            resDict["path"] = os.path.abspath(os.path.join(Model_Dir, filename))
            model_files[alg] = resDict

    return model_files


Model_Files = __get_Model_Files()


class ClassifierMixin(object, metaclass=Singleton):

    Algorithm = ""

    def __init__(self):
        if self.__class__ == __class__:
            raise ABCNotImplementedError
        clf, feature = self.__load_model()
        self._clf = clf
        self.feature = feature

    @classmethod
    def __load_model(cls):
        alg = cls.Algorithm
        detail = Model_Files.get(alg)
        path, fCode, lCode = map(detail.__getitem__, ["path","feature","level"])
        feature = FeatureExtractor.get_feature(fCode, lCode)
        if path is None:
            raise ModelFileNotFoundError("Model %s.* is mising !" % alg)
        return joblib.load(path), feature

    def predict(self, Xlist):
        return self._clf.predict(Xlist)


class RandomForest(ClassifierMixin):
    Algorithm = "RandomForest"

class KNN(ClassifierMixin):
    Algorithm = "KNN"

class SVM(ClassifierMixin):
    Algorithm = "SVM"