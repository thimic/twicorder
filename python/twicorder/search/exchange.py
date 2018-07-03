#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

from datetime import datetime
from queue import Queue
from threading import Thread


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RateLimitCentral(object, metaclass=Singleton):

    def __init__(self):
        self._limits = {}

    def update(self, endpoint, header):
        self._limits[endpoint] = RateLimit(header)

    def get(self, endpoint):
        return self._limits.get(endpoint)

    def get_cap(self, endpoint):
        limit = self.get(endpoint)
        if not limit:
            return
        return limit.cap

    def get_remaining(self, endpoint):
        limit = self.get(endpoint)
        if not limit:
            return
        return limit.remaining

    def get_reset(self, endpoint):
        limit = self.get(endpoint)
        if not limit:
            return
        return limit.reset


class RateLimit(object):

    def __init__(self, headers):
        self._cap = headers.get('x-rate-limit-limit')
        self._remaining = headers.get('x-rate-limit-remaining')
        self._reset = (
            datetime.fromtimestamp(int(headers.get('x-rate-limit-reset')))
        )

    def __repr__(self):
        representation = (
            f'RateLimit(cap={self.cap}, remaining={self.remaining}, '
            f'reset="{self.reset:%y.%m.%d %H:%M:%S}")'
        )
        return representation

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def cap(self):
        return self._cap

    @property
    def remaining(self):
        return self._remaining

    @property
    def reset(self):
        return self._reset


class MultiPart(object):

    def __init__(self, query):
        self._query = query

    @property
    def query(self):
        return self._query

    @property
    def max_count(self):
        return self.query.max_count

    def run(self):
        while True:
            response = self.query.run()
            content = response.content.decode()
            data = json.loads(content)
            if len(data) < self.max_count:
                break


class WorkerDispatch(object):

    @classmethod
    def get(cls, queue):
        def worker():
            while True:
                query = queue.get()
                if query is None:
                    import inspect
                    stack = inspect.stack()
                    the_class = stack[1][0].f_locals['self']
                    print(f'Terminating thread "{the_class.name}"')
                    break
                data = cls.run_query(query)
                print(query.request_url, len(data))
                print(RateLimitCentral().get(query.endpoint))
                queue.task_done()
        return worker

    @classmethod
    def run_query(cls, query):
        response = query.run()
        content = response.content.decode()
        data = json.loads(content)
        headers = response.headers
        RateLimitCentral().update(query.endpoint, headers)
        return data


class QueryExchange(object):

    def __init__(self):
        self._queues = {}
        self._threads = []

    @property
    def queues(self):
        return self._queues

    @property
    def threads(self):
        return self._threads

    def get_queue(self, endpoint):
        if not self._queues.get(endpoint):
            queue = Queue()
            self._queues[endpoint] = queue
            thread = Thread(target=WorkerDispatch.get(queue), name=endpoint)
            thread.start()
            self._threads.append(thread)
        return self._queues[endpoint]

    def add(self, query):
        queue = self.get_queue(query.endpoint)
        queue.put(query)

    def wait(self):
        for queue in self.queues.values():
            queue.put(None)
        # for queue in self.queues.values():
        #     queue.join()
        for thread in self.threads:
            thread.join()


if __name__ == '__main__':
    from twicorder.auth import get_auth_handler
    from twicorder.search.queries.request_queries import TimelineQuery
    from twicorder.utils import write

    auth = get_auth_handler()
    accounts = [
        'slpng_giants',
        'slpng_giants_no',
        'slpng_giants_se',
        'slpng_giants_eu',
        'slpng_giants_nz'
    ]
    queries = TimelineQuery(auth)

    qe = QueryExchange()
    for account in accounts:
        qe.add(TimelineQuery(auth, screen_name=account))
    qe.wait()
