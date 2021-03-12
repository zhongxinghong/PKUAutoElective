#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: cnn.py
# modified: 2020-02-15

import torch
import torch.nn as nn
import torch.nn.functional as F

class CaptchaCNN(nn.Module):

    CAPTCHA_LABELS = '2345678abcdefghklmnpqrstuvwxy'

    def __init__(self):
        super().__init__()
        self.bn0 = nn.BatchNorm2d(1)
        self.bn1 = nn.BatchNorm2d(16)
        self.bn2 = nn.BatchNorm2d(32)
        self.bn3 = nn.BatchNorm2d(64)
        self.bn4 = nn.BatchNorm2d(128)
        self.bn5 = nn.BatchNorm2d(256)
        self.bn6 = nn.BatchNorm2d(512)
        self.conv1 = nn.Conv2d(1, 16, 3)
        self.conv2 = nn.Conv2d(16, 32, 3)
        self.conv3 = nn.Conv2d(32, 64, 3)
        self.conv4 = nn.Conv2d(64, 128, 3)
        self.conv5 = nn.Conv2d(128, 256, 3)
        self.conv6 = nn.Conv2d(256, 512, 3)
        self.fc1 = nn.Linear(2048, 512)
        self.fc2 = nn.Linear(512, 128)
        self.fc3 = nn.Linear(128, len(self.CAPTCHA_LABELS)) # 29

    def forward(self, x):
        x = self.bn0(x)         # batch*1*52*52
        x = F.relu(x)
        x = self.conv1(x)       # batch*16*50*50
        x = self.bn1(x)
        x = F.relu(x)
        x = self.conv2(x)       # batch*32*48*48
        x = self.bn2(x)
        x = F.relu(x)
        x = F.avg_pool2d(x, 2)  # batch*32*24*24
        x = self.conv3(x)       # batch*64*22*22
        x = self.bn3(x)
        x = F.relu(x)
        x = self.conv4(x)       # batch*128*20*20
        x = self.bn4(x)
        x = F.relu(x)
        x = F.avg_pool2d(x, 2)  # batch*128*10*10
        x = self.conv5(x)       # batch*256*8*8
        x = self.bn5(x)
        x = F.relu(x)
        x = F.avg_pool2d(x, 2)  # batch*256*4*4
        x = self.conv6(x)       # batch*512*2*2
        x = self.bn6(x)
        x = F.relu(x)
        x = torch.flatten(x, 1) # batch*2048
        x = self.fc1(x)         # batch*512
        x = F.relu(x)
        x = self.fc2(x)         # batch*128
        x = F.relu(x)
        x = self.fc3(x)         # batch*29
        x = F.log_softmax(x, dim=1)
        return x
