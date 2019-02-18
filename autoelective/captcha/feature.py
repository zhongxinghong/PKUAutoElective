#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: captcha/feature.py

from functools import partial
from PIL import Image
import numpy as np
from ..util import NoInstance
from ..exceptions import FeatureCodeError

__all__ = ["FeatureExtractor",]


class FeatureExtractor(object, metaclass=NoInstance):

    @staticmethod
    def get_feature(feature, level=""):
        Feature_Map = {
            "1": __class__.feature1,
            "2": __class__.feature2,
            "3": __class__.feature3,
            "4": __class__.feature4,
            "5": __class__.feature5,
        }
        feature = str(feature)
        if feature in ("1","2"):
            func = Feature_Map[feature]
        elif feature in ("3","4","5"):
            if level == "":
                raise FeatureCodeError
            level = int(level)
            if not 1 <= level:
                raise FeatureCodeError
            func = partial(Feature_Map[feature], level=level)
        return func

    @staticmethod
    def feature1(img):
        """ 遍历全部像素 """
        ary = np.array(img.convert("1"))
        ary = 1 - ary # 反相
        return ary.flatten()

    @staticmethod
    def feature2(img):
        """ feature2 降维 """
        ary = np.array(img.convert("1"))
        ary = 1 - ary # 反相
        return np.concatenate([ary.sum(axis=0), ary.sum(axis=1)])

    @staticmethod
    def feature3(img, level):
        """ 考虑临近像素的遍历 """
        ary = np.array(img.convert("1"))
        ary = 1 - ary # 反相
        l = level
        featureVector = []
        for i in range(l, ary.shape[0]-l):
            for j in range(l, ary.shape[1]-l):
                i1,i2,j1,j2 = i-l, i+l+1, j-l, j+l+1
                featureVector.append(np.sum(ary[i1:i2, j1:j2])) # sum block
        return np.array(featureVector)

    @staticmethod
    def feature4(img, level):
        """ feature3 降维 """
        ary = __class__.feature3(img, level)
        s = int(np.sqrt(ary.size))
        assert s**2 == ary.size # 确保为方
        ary.resize((s,s))
        return np.concatenate([ary.sum(axis=0), ary.sum(axis=1)])

    @staticmethod
    def feature5(img, level):
        """ feature3 改版，给接近中心的点增加权重

            weight 矩阵例如：
            array([[1, 1, 1, 1, 1],
                   [1, 2, 2, 2, 1],
                   [1, 2, 3, 2, 1],
                   [1, 2, 2, 2, 1],
                   [1, 1, 1, 1, 1]])
        """
        ary = np.array(img.convert("1"))
        ary = 1 - ary # 反相
        l = level
        s = size = 2 * l + 1
        weight = np.zeros(s**2,dtype=np.int).reshape((s,s))
        for k in range(l+1):
            mask = np.array([k<=i<s-k and k<=j<s-k for i in range(s) for j in range(s)]).reshape((s,s))
            weight[mask] += (k + 1)**2 # 等比数列
        featureVector = []
        for i in range(l, ary.shape[0]-l):
            for j in range(l, ary.shape[1]-l):
                i1,i2,j1,j2 = i-l, i+l+1, j-l, j+l+1
                featureVector.append(np.sum(ary[i1:i2, j1:j2]*weight)) # sum block with weight
        return np.array(featureVector)
