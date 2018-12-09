#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.web.browser import app
from twicorder.utils import FileLogger


if __name__ == '__main__':
    try:
        app.run('localhost')
    except Exception:
        logger = FileLogger.get()
        logger.exception('TwiBrowser Error: ')

