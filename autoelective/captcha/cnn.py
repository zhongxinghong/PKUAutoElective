#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: cnn.py
# modified: 2020-02-15

import torch
import torch.nn as nn
import torch.nn.functional as F

class CNN(nn.Module):

    LABELS = (
        '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
        'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a',
        'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'm', 'n', 'p', 'q', 'r', 's',
        't', 'u', 'v', 'w', 'x', 'y', 'z',
    )

    def __init__(self):
        super().__init__()
        self.bn1 = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)
        self.conv1 = nn.Conv2d(1, 32, 3)
        self.conv2 = nn.Conv2d(32, 64, 3)
        self.conv3 = nn.Conv2d(64, 128, 3)
        self.fc1 = nn.Linear(512, 128)
        self.fc2 = nn.Linear(128, len(self.LABELS)) # 55

    def forward(self, x):
        x = self.conv1(x)       # batch*32*20*20
        x = self.bn1(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)  # batch*32*10*10
        x = self.conv2(x)       # batch*64*8*8
        x = self.bn2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)  # batch*64*4*4
        x = self.conv3(x)       # batch*128*2*2
        x = self.bn3(x)
        x = F.relu(x)
        x = torch.flatten(x, 1) # batch*512
        x = self.fc1(x)         # batch*128
        x = F.relu(x)
        x = self.fc2(x)         # batch*55
        x = F.log_softmax(x, dim=1)
        return x
