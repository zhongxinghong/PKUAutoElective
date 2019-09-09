#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: processor.py
# modified: 2019-09-08

__all__ = [

    "denoise8","denoise24","crop",

    "STEPS4","STEPS8","STEPS24",

    ]

from PIL import Image


_STEPS_LAYER_1 = ((1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1))
_STEPS_LAYER_2 = ((2,2),(2,1),(2,0),(2,-1),(2,-2),(1,2),(1,-2),(0,2),(0,-2),(-1,2),(-1,-2),(-2,2),(-2,1),(-2,0),(-2,-1),(-2,-2))

STEPS4  = ((0,1),(0,-1),(1,0),(-1,0))
STEPS8  = _STEPS_LAYER_1
STEPS24 = _STEPS_LAYER_1 + _STEPS_LAYER_2

_PX_WHITE = 255
_PX_Black = 0

_DEFAULT_MIN_BLOCK_SIZE = 9


def _assert_image_mode_equals_to_1(img):
    assert img.mode == "1", "image mode must be '1', not %s" % img.mode


def _denoise(img, steps, threshold, repeat):
    """ 去噪函数模板 """
    _assert_image_mode_equals_to_1(img)

    for _ in range(repeat):
        for j in range(img.width):
            for i in range(img.height):
                px = img.getpixel((j,i))
                if px == _PX_WHITE: # 自身白
                    continue
                count = 0
                for x, y in steps:
                    j2 = j + y
                    i2 = i + x
                    if 0 <= j2 < img.width and 0 <= i2 < img.height: # 边界内
                        if img.getpixel((j2,i2)) == _PX_WHITE: # 周围白
                            count += 1
                    else: # 边界外全部视为黑
                        count += 1
                if count >= threshold:
                   img.putpixel((j,i), _PX_WHITE)

    return img


def denoise8(img, steps=STEPS8, threshold=6, repeat=2):
    """ 考虑外一周的降噪 """
    return _denoise(img, steps, threshold, repeat)


def denoise24(img, steps=STEPS24, threshold=20, repeat=2):
    """ 考虑外两周的降噪 """
    return _denoise(img, steps, threshold, repeat)


def _search_blocks(img, steps=STEPS8, min_block_size=_DEFAULT_MIN_BLOCK_SIZE):
    """ 找到图像中的所有块 """
    _assert_image_mode_equals_to_1(img)

    marked = [ [ 0 for j in range(img.width) ] for i in range(img.height) ]


    def _is_marked(i,j):
        if marked[i][j]:
            return True
        else:
            marked[i][j] = 1
            return False


    def _is_white_px(i,j):
        return img.getpixel((j,i)) == _PX_WHITE


    def _queue_search(i,j):
        """ 利用堆栈寻找字母 """
        queue = [(j,i),]
        head = 0
        while head < len(queue):
            now = queue[head]
            head += 1
            for x, y in steps:
                j2 = now[0] + y
                i2 = now[1] + x
                if 0 <= j2 < img.width and 0 <= i2 < img.height:
                    if _is_marked(i2,j2) or _is_white_px(i2,j2):
                        continue
                    queue.append((j2,i2))
        return queue


    blocks = []
    for j in range(img.width):
        for i in range(img.height):
            if _is_marked(i,j) or _is_white_px(i,j):
                continue
            block = _queue_search(i,j)
            if len(block) >= min_block_size:
                js = [ j for j, _ in block ]
                blocks.append( (block, min(js), max(js)) )

    assert 1 <= len(blocks) <= 4, "unexpected number of captcha blocks: %s" % len(blocks)

    return blocks


def _split_spans(spans):
    """ 确保 spans 为 4 份 """
    assert 1 <= len(spans) <= 4, "unexpected number of captcha blocks: %s" % len(spans)

    if len(spans) == 1: # 四等分
        totalSpan = spans[0]
        delta = (totalSpan[1] - totalSpan[0]) // 4
        spans = [
            (totalSpan[0],         totalSpan[0]+delta  ),
            (totalSpan[0]+delta,   totalSpan[0]+delta*2),
            (totalSpan[1]-delta*2, totalSpan[1]-delta  ),
            (totalSpan[1]-delta,   totalSpan[1]        ),
        ]

    if len(spans) == 2: # 三等分较大块
        maxSpan = max(spans, key=lambda span: span[1]-span[0])
        idx = spans.index(maxSpan)
        delta = (maxSpan[1] - maxSpan[0]) // 3
        spans.remove(maxSpan)
        spans.insert(idx,   (maxSpan[0],       maxSpan[0]+delta))
        spans.insert(idx+1, (maxSpan[0]+delta, maxSpan[1]-delta))
        spans.insert(idx+2, (maxSpan[1]-delta, maxSpan[1]      ))

    if len(spans) == 3: # 平均均分较大块
        maxSpan = max(spans, key=lambda span: span[1]-span[0])
        idx = spans.index(maxSpan)
        mid = sum(maxSpan) // 2
        spans.remove(maxSpan)
        spans.insert(idx,   (maxSpan[0], mid))
        spans.insert(idx+1, (mid, maxSpan[1]))

    if len(spans) == 4:
        pass

    return spans


def _crop(img, spans):
    """ 分割图片 """
    _assert_image_mode_equals_to_1(img)
    assert len(spans) == 4, "unexpected number of captcha blocks: %s" % len(spans)

    size = img.height # img.height == 22
    segs = []

    for left, right in spans:
        quadImg = Image.new("1", (size,size), _PX_WHITE)
        segImg = img.crop((left, 0, right+1, size))  # left, upper, right, and lower
        quadImg.paste(segImg, ( (size-segImg.width) // 2, 0 ))  # a 2-tuple giving the upper left corner
        segs.append(quadImg)

    return segs


def crop(img):
    _assert_image_mode_equals_to_1(img)

    blocks = _search_blocks(img, steps=STEPS8)
    spans = [i[1:] for i in blocks]
    spans.sort(key=lambda span: sum(span))
    spans = _split_spans(spans)
    segs = _crop(img, spans)

    return segs, spans
