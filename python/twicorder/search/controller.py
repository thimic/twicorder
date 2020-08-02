#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import traceback

from twicorder.search.scheduler import Scheduler
from twicorder.utils import TwiLogger


class Twicorder(object):

    def __init__(self):
        self._scheduler = Scheduler()

    def run(self):
        self._scheduler.run()


if __name__ == '__main__':
    twicorder = Twicorder()
    twicorder.run()
    # while True:
    #     try:
    #         twicorder = Twicorder()
    #         twicorder.run()
    #     except Exception:
    #         TwiLogger.exception(traceback.format_exc())
    #         TwiLogger.critical('A fatal error occured. Restarting TwiCorder.')
    #     time.sleep(10)

