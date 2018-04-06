#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import os

THIS_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))

TW_TIME_FORMAT = '%a %b %d %H:%M:%S %z %Y'

REGULAR_EXTENSIONS = ['txt', 'json', 'yaml', 'twc']
COMPRESSED_EXTENSIONS = ['gzip', 'zip', 'twzip']

COMPANY = 'Zhenyael'
APP = 'TwiCorder'
