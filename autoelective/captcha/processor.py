#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: processor.py
# modified: 2019-09-08

import cv2
import numpy as np
from io import BytesIO
from PIL import Image


def extract_c0(M0, M_merge):
    _, M_mask = cv2.threshold(M_merge, 0, 0xff, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    M_mask[:, 40:] = 0xff
    M_darken = M0.copy()
    M_darken[M_mask == 0x00] >>= 1

    _, M_threshold = cv2.threshold(M_darken, 0, 0xff, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    kernel1 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
    M_close1 = cv2.morphologyEx(M_threshold, cv2.MORPH_CLOSE, kernel1, iterations=1)
    M_blur1 = cv2.medianBlur(M_close1, 3)

    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2))
    M_close2 = cv2.morphologyEx(M_threshold, cv2.MORPH_CLOSE, kernel2, iterations=1)
    M_blur2 = cv2.medianBlur(M_close2, 3)

    if np.sum(M_blur1[:, :40]) <= np.sum(M_blur2[:, :40]):
        Mt = M_blur1
    else:
        Mt = M_blur2
    return Mt


def extract_c123(M0, M0_last):
    M_subtract = cv2.subtract(M0_last, M0)

    _, M_threshold = cv2.threshold(M_subtract, 0, 0xff, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    M_opened = cv2.morphologyEx(M_threshold, cv2.MORPH_OPEN, kernel, iterations=1)

    Mt = cv2.medianBlur(M_opened, 3)
    return Mt


def crop(Mt, first):
    char_width = 32
    captcha_size = 52

    assert Mt.shape[0] == captcha_size

    M_blur = cv2.medianBlur(Mt, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (11, 11))
    M_opened = cv2.morphologyEx(M_blur, cv2.MORPH_OPEN, kernel, iterations=3)

    w = 50 if first else Mt.shape[1]

    S0 = (0xff - M_opened).sum(axis=0).cumsum()
    k = char_width

    max_sum = -1
    max_pos = -1

    for i in range(k, w):
        s = S0[i] - S0[i - k]
        if s > max_sum:
            max_sum = s
            max_pos = i

    w = max_pos - k - (captcha_size - k) // 2

    if w >= 0 and w + captcha_size <= Mt.shape[1]:
        return Mt[:, w : w+captcha_size]

    M_cropped = 0xff - np.zeros((captcha_size, captcha_size), np.uint8)
    if w < 0:
        M_cropped[:, -w : captcha_size] = Mt[:, : captcha_size+w]
    else:
        M_cropped[:, : Mt.shape[1]-w] = Mt[:, w :]
    return M_cropped


def split_captcha(im_data):
    assert isinstance(im_data, bytes)

    fp = BytesIO(im_data)
    im = Image.open(fp)

    assert im.format == "GIF", im.format
    assert im.n_frames == 16, im.n_frames

    N = 52
    w, h = im.size

    M0_list = []
    M0_last = None
    M_mask = np.zeros((h, w), dtype=np.uint8)
    M_merge = np.full((h, w), 0xff, dtype=np.uint8)
    Xlist = []

    for ix in (3, 7, 11, 15):
        im.seek(ix)
        M0 = np.array(im.convert('RGB'))
        M0 = cv2.cvtColor(M0, cv2.COLOR_RGB2GRAY)
        M0_list.append(M0)
        M_merge = np.min([M_merge, M0], axis=0)

    for cix, M0 in enumerate(M0_list):
        first = (M0_last is None)

        if first:
            Mt = extract_c0(M0, M_merge)
        else:
            Mt = extract_c123(M0, M0_last)

        M0_last = M0

        Mt_inv = 0xff - Mt
        Mt = 0xff - np.bitwise_and(Mt_inv, 0xff - M_mask)
        M_mask = np.bitwise_or(M_mask, Mt_inv)

        Mt = crop(Mt, first)

        Xlist.append(Mt)

    im.close()
    fp.close()

    return Xlist
