#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复测试文件的编码问题
"""

import sys

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("编码设置完成")
