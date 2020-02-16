#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: processor.py
# modified: 2019-09-08

from PIL import Image

_STEPS_LAYER_1 = [(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)]
_STEPS_LAYER_2 = [(2,2),(2,1),(2,0),(2,-1),(2,-2),(1,2),(1,-2),(0,2),(0,-2),
                    (-1,2),(-1,-2),(-2,2),(-2,1),(-2,0),(-2,-1),(-2,-2)]
STEPS4  = [(0,1),(0,-1),(1,0),(-1,0)]
STEPS8  = _STEPS_LAYER_1
STEPS24 = _STEPS_LAYER_1 + _STEPS_LAYER_2

_PX_WHITE = 255
_PX_BLACK = 0

_DEFAULT_MIN_BLOCK_SIZE = 9

_BLOCKS_NUMBER_ERROR = "unexpected number of captcha blocks: %d"

def _assert_image_mode_equals_to_1(im):
    assert im.mode == "1", "image mode must be '1', not %s" % im.mode


def _denoise(im, steps, threshold, repeat):
    """ 去噪函数模板 """
    _assert_image_mode_equals_to_1(im)

    width, height = im.size
    data = im.load()

    for _ in range(repeat):
        for j in range(width):
            for i in range(height):
                px = data[j, i]
                if px == _PX_WHITE: # 自身白
                    continue
                cnt = 0
                for x, y in steps:
                    j2 = j + y
                    i2 = i + x
                    if 0 <= j2 < width and 0 <= i2 < height: # 边界内
                        if data[j2, i2] == _PX_WHITE: # 周围白
                            cnt += 1
                    else: # 边界外全部视为黑
                        cnt += 1
                if cnt >= threshold:
                    data[j, i] = _PX_WHITE

    return im


def denoise8(im, steps=STEPS8, threshold=6, repeat=2):
    """ 考虑外一周的降噪 """
    return _denoise(im, steps, threshold, repeat)


def denoise24(im, steps=STEPS24, threshold=20, repeat=2):
    """ 考虑外两周的降噪 """
    return _denoise(im, steps, threshold, repeat)


def _search_blocks(im, steps=STEPS8, min_block_size=_DEFAULT_MIN_BLOCK_SIZE):
    """ 找到图像中的所有块 """
    _assert_image_mode_equals_to_1(im)

    width, height = im.size
    data = im.load()

    marked = [ [ False for j in range(width) ] for i in range(height) ]

    def _test_and_mark(i, j):
        if marked[i][j]:
            return False
        marked[i][j] = True
        if data[j, i] == _PX_WHITE:
            return False
        return True

    def _search(i, j):
        block = [(j,i),] # queue search
        head = 0
        while head < len(block):
            now = block[head]
            head += 1
            for x, y in steps:
                j = now[0] + y
                i = now[1] + x
                if 0 <= j < width and 0 <= i < height and _test_and_mark(i, j):
                    block.append((j,i))
        return block

    blocks = []
    for j in range(width):
        for i in range(height):
            if not _test_and_mark(i, j):
                continue
            block = _search(i, j)
            if len(block) >= min_block_size:
                js = [ _j for (_j, _) in block ]
                blocks.append( (block, min(js), max(js)) )

    assert 1 <= len(blocks) <= 4, _BLOCKS_NUMBER_ERROR % len(blocks)

    return blocks


def _split_spans(spans):
    """ 确保 spans 为 4 份 """
    assert 1 <= len(spans) <= 4, _BLOCKS_NUMBER_ERROR % len(spans)

    spans.sort(key=lambda s: sum(s))

    if len(spans) == 1: # 四等分
        maxs = spans[0]
        d = (maxs[1] - maxs[0]) // 4
        spans.remove(maxs)
        spans.extend([
            (maxs[0],     maxs[0]+d  ),
            (maxs[0]+d,   maxs[0]+d*2),
            (maxs[1]-d*2, maxs[1]-d  ),
            (maxs[1]-d,   maxs[1]    ),
        ])

    if len(spans) == 2: # 三等分较大块
        maxs = max(spans, key=lambda s: s[1] - s[0])
        d = (maxs[1] - maxs[0]) // 3
        spans.remove(maxs)
        spans.extend([
            (maxs[0],   maxs[0]+d),
            (maxs[0]+d, maxs[1]-d),
            (maxs[1]-d, maxs[1]  ),
        ])

    if len(spans) == 3: # 平均均分较大块
        maxs = max(spans, key=lambda s: s[1] - s[0])
        mid = sum(maxs) // 2
        spans.remove(maxs)
        spans.extend([
            (maxs[0], mid    ),
            (mid,     maxs[1]),
        ])

    spans.sort(key=lambda s: sum(s))

    return spans


def _crop(im, spans):
    """ 分割图片 """
    _assert_image_mode_equals_to_1(im)
    assert len(spans) == 4, _BLOCKS_NUMBER_ERROR % len(spans)
    assert im.height == 22

    N = im.height
    segs = []

    for st, ed in spans:
        qim = Image.new("1", (N, N), _PX_WHITE)
        sim = im.crop((st, 0, ed+1, N))  # (left, upper, right, lower)
        qim.paste(sim, ( (N-sim.width) // 2, 0 ))  # a 2-tuple giving the upper left corner
        segs.append(qim)

    return segs


def crop(im):
    _assert_image_mode_equals_to_1(im)

    blocks = _search_blocks(im, steps=STEPS8)
    spans = [ (st, ed) for (_, st, ed) in blocks ]
    spans = _split_spans(spans)
    segs = _crop(im, spans)

    return segs, spans
