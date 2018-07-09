#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.search.exchange import QueryExchange
from twicorder.search.scheduler import Scheduler


class Twicorder(object):

    def __init__(self):
        self._query_exchange = QueryExchange()
        self._scheduler = Scheduler()

    def run(self):
        pass


if __name__ == '__main__':
    twicorder = Twicorder()
    twicorder.run()
