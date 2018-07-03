#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.search.queries import TweepyQuery


class RateLimitStatusQuery(TweepyQuery):

    _endpoint = '/application/rate_limit_status'

    def run(self):
        self._response = self.api.rate_limit_status()


class TimelineQuery(TweepyQuery):

    _endpoint = '/statuses/user_timeline'

    def run(self):
        self._response = self.api.user_timeline(*self.args, **self.kwargs)
        return self._response
