#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: captcha/preprocess.py

import os
from PIL import Image
from ..util import NoInstance
from ..exceptions import ImageModeError, ImageBlocksNumException

__all__ = ["ImageProcessor",]


class ImageProcessor(object, metaclass=NoInstance):
    """ 图像处理类，提供验证码的降噪和切割

        public  static method   denoise8
                                denoise24
                                crop

        private static method   _denoise
                                _search_blocks
                                _split_spans
                                _crop
    """
    PX_White = 255
    PX_Black = 0

    StepsLayer1 = ((1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1))
    StepsLayer2 = ((2,2),(2,1),(2,0),(2,-1),(2,-2),(1,2),(1,-2),(0,2),\
                   (0,-2),(-1,2),(-1,-2),(-2,2),(-2,1),(-2,0),(-2,-1),(-2,-2))
    Steps4  = ((0,1), (0,-1),(1,0), (-1,0))
    Steps8  = StepsLayer1
    Steps24 = StepsLayer1 + StepsLayer2

    Min_Block_Size = 9

    @staticmethod
    def _denoise(img, steps, threshold, repeat):
        """ 去噪函数模板 """
        if not img.mode == "1":
            raise ImageModeError
        for _ in range(repeat):
            for j in range(img.width):
                for i in range(img.height):
                    px = img.getpixel((j,i))
                    if px == __class__.PX_White: # 自身白
                        continue
                    count = 0
                    for x, y in steps:
                        j2 = j + y
                        i2 = i + x
                        if 0 <= j2 < img.width and 0 <= i2 < img.height: # 边界内
                            if img.getpixel((j2,i2)) == __class__.PX_White: # 周围白
                                count += 1
                        else: # 边界外全部视为黑
                            count += 1
                    if count >= threshold:
                       img.putpixel((j,i), __class__.PX_White)
        return img

    @staticmethod
    def denoise8(img, steps=Steps8, threshold=6, repeat=2):
        """ 考虑外一周的降噪 """
        return __class__._denoise(img, steps, threshold, repeat)

    @staticmethod
    def denoise24(img, steps=Steps24, threshold=20, repeat=2):
        """ 考虑外两周的降噪 """
        return __class__._denoise(img, steps, threshold, repeat)

    @staticmethod
    def _search_blocks(img, steps=Steps8, min_block_size=Min_Block_Size):
        """ 找到图像中的所有块 """
        if not img.mode == "1":
            raise ImageModeError

        marked = [[0 for j in range(img.width)] for i in range(img.height)]

        def _is_marked(i,j):
            if marked[i][j]:
                return True
            else:
                marked[i][j] = 1
                return False

        def _is_white_px(i,j):
            return img.getpixel((j,i)) == __class__.PX_White

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
                    js = [j for j,i in block]
                    blocks.append( (block, min(js), max(js)) )

        if not 1 <= len(blocks) <= 4:
            raise ImageBlocksNumException
        return blocks

    @staticmethod
    def _split_spans(spans):
        """ 确保 spans 为 4 份 """
        if not 1 <= len(spans) <= 4:
            raise ImageBlocksNumException
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

    @staticmethod
    def _crop(img, spans):
        """ 分割图片 """
        if not img.mode == "1":
            raise ImageModeError
        if not len(spans) == 4:
            raise ImageBlocksNumException
        size = img.height # img.height == 22
        segs = []
        for left, right in spans:
            quadImg = Image.new("1", (size,size), __class__.PX_White)
            segImg = img.crop((left, 0, right+1, size)) # left, upper, right, and lower
            quadImg.paste(segImg, ( (size-segImg.width) // 2, 0 )) # a 2-tuple giving the upper left corner
            segs.append(quadImg)
        return segs

    @staticmethod
    def crop(img):
        if not img.mode == "1":
            raise ImageModeError
        blocks = __class__._search_blocks(img, steps=__class__.Steps8)
        spans = [i[1:] for i in blocks]
        spans.sort(key=lambda span: sum(span))
        spans = __class__._split_spans(spans)
        segs = __class__._crop(img, spans)
        return segs, spans
