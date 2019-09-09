#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: feature.py
# modified: 2019-09-08

__all__ = ["get_feature_extractor"]

from functools import partial
import numpy as np


def _feature1(img):
    """ 遍历全部像素 """
    ary = np.array(img.convert("1"))
    ary = 1 - ary # 反相
    return ary.flatten()


def _feature2(img):
    """ feature2 降维 """
    ary = np.array(img.convert("1"))
    ary = 1 - ary # 反相
    return np.concatenate([ary.sum(axis=0), ary.sum(axis=1)])


def _feature3(img, level):
    """ 考虑临近像素的遍历 """
    ary = np.array(img.convert("1"))
    ary = 1 - ary # 反相
    l = level
    featureVector = []
    for i in range(l, ary.shape[0]-l):
        for j in range(l, ary.shape[1]-l):
            i1, i2, j1, j2 = i-l, i+l+1, j-l, j+l+1
            featureVector.append(np.sum(ary[i1:i2, j1:j2])) # sum block
    return np.array(featureVector)


def _feature4(img, level):
    """ feature3 降维 """
    ary = _feature3(img, level)
    s = int(np.sqrt(ary.size))
    assert s**2 == ary.size # 确保为方
    ary.resize((s,s))
    return np.concatenate([ary.sum(axis=0), ary.sum(axis=1)])


def _feature5(img, level):
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
    weight = np.zeros(s**2, dtype=np.int).reshape((s,s))
    for k in range(l+1):
        mask = np.array([ k <= i < s-k and k <= j < s-k for i in range(s) for j in range(s) ]).reshape((s,s))
        weight[mask] += (k + 1)**2 # 等比数列
    featureVector = []
    for i in range(l, ary.shape[0]-l):
        for j in range(l, ary.shape[1]-l):
            i1, i2, j1, j2 = i-l, i+l+1, j-l, j+l+1
            featureVector.append(np.sum(ary[i1:i2, j1:j2]*weight)) # sum block with weight
    return np.array(featureVector)



_FEATURE_MAP = {

    "1": _feature1,
    "2": _feature2,
    "3": _feature3,
    "4": _feature4,
    "5": _feature5,
}


def get_feature_extractor(feature, level=""):
    feature = str(feature)
    if feature in ("1","2"):
        func = _FEATURE_MAP[feature]
    elif feature in ("3","4","5"):
        if level == "":
            raise ValueError("level must be given for feature %s" % feature)
        level = int(level)
        if level <= 0:
            raise ValueError("level must be a positive integer, not %s" % level)
        func = partial(_FEATURE_MAP[feature], level=level)
    return func
