#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.search.scheduler import Scheduler


class Twicorder(object):

    def __init__(self):
        self._scheduler = Scheduler()

    def run(self):
        self._scheduler.run()


if __name__ == '__main__':
    twicorder = Twicorder()
    twicorder.run()
