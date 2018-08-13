#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import traceback

from twicorder.search.scheduler import Scheduler
from twicorder.utils import FileLogger

logger = FileLogger.get()


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
    #         logger.exception(traceback.format_exc())
    #         logger.critical('A fatal error occured. Restarting TwiCorder.')
    #     time.sleep(10)

