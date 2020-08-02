#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.web.browser import app
from twicorder.utils import TwiLogger


if __name__ == '__main__':
    try:
        app.run('localhost')
    except Exception:
        TwiLogger.exception('TwiBrowser Error: ')

