#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

from datetime import datetime
from queue import Queue
from threading import Thread

from twicorder.utils import Singleton, FileLogger

logger = FileLogger.get()


class RateLimitCentral(object, metaclass=Singleton):

    def __init__(self):
        self._limits = {}

    def update(self, endpoint, header):
        limit_keys = {
            'x-rate-limit-limit',
            'x-rate-limit-remaining',
            'x-rate-limit-reset'
        }
        if not limit_keys.issubset(header.keys()):
            return
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
    """
    Rate limit object, used to describe the limits for a given API end point.
    """

    def __init__(self, headers):
        self._cap = headers.get('x-rate-limit-limit')
        self._remaining = int(headers.get('x-rate-limit-remaining'))
        self._reset = float(headers.get('x-rate-limit-reset'))

    def __repr__(self):
        reset = datetime.fromtimestamp(self._reset)
        representation = (
            f'RateLimit(cap={self.cap}, remaining={self.remaining}, '
            f'reset="{reset:%y.%m.%d %H:%M:%S}")'
        )
        return representation

    @property
    def cap(self):
        """
        Queries allowed per 15 minutes.

        Returns:
            int: Number of queries

        """
        return self._cap

    @property
    def remaining(self):
        """
        Queries left for the current 15 minute window.

        Returns:
            int: Number of queries

        """
        return self._remaining

    @property
    def reset(self):
        """
        Time until the current 15 minute window expires.

        Returns:
            float: Reset time

        """
        return self._reset


class QueryWorker(Thread):
    """
    Queue thread, used to execute queue queries.
    """

    def __init__(self, *args, **kwargs):
        super(QueryWorker, self).__init__(*args, **kwargs)
        self._query = None

    def setup(self, queue):
        self._queue = queue

    @property
    def queue(self):
        return self._queue

    @property
    def query(self):
        return self._query

    def run(self):
        """
        Fetches query from queue and executes it.
        """
        while True:
            self._query = self.queue.get()
            if self.query is None:
                logger.info(f'Terminating thread "{self.name}"')
                break
            while not self.query.done:
                try:
                    self.query.run()
                except Exception:
                    import traceback
                    logger.exception(traceback.format_exc())
                logger.info(self.query.fetch_log())
                time.sleep(.2)
            time.sleep(.5)
            self.queue.task_done()


class QueryExchange(object):
    """
    Organises queries in queues and executes them after the FIFO princible.
    """
    def __init__(self):
        self._queues = {}
        self._threads = {}

    @property
    def queues(self):
        return self._queues

    @property
    def threads(self):
        return self._threads

    def get_queue(self, endpoint):
        """
        Retrieves the queue for the given endpoint if it exists, otherwise
        creates a queue.

        Args:
            endpoint (str): API endpoint

        Returns:
            Queue: Queue for endpoint

        """
        if not self._queues.get(endpoint):
            queue = Queue()
            self._queues[endpoint] = queue
            thread = QueryWorker(name=endpoint)
            thread.setup(queue=queue)
            thread.start()
            self._threads[endpoint] = thread
        return self._queues[endpoint]

    def add(self, query):
        """
        Finds appropriate queue for given end point and adds it.

        Args:
            query (BaseQuery): Query object

        """
        queue = self.get_queue(query.endpoint)
        if query in queue.queue:
            logger.info(f'Query with ID {query.uid} is already in the queue.')
            return
        thread = self.threads.get(query.endpoint)
        if thread and thread.query == query:
            logger.info(f'Query with ID {query.uid} is already running.')
            return
        queue.put(query)
        logger.info(query)

    def wait(self):
        """
        Sends shutdown signal to threads and waits for all threads and queues to
        terminate.
        """
        for queue in self.queues.values():
            queue.put(None)
        # for queue in self.queues.values():
        #     queue.join()
        for thread in self.threads.values():
            thread.join()


if __name__ == '__main__':
    from twicorder.auth import get_auth_handler
    from twicorder.search.queries.request_queries import TimelineQuery
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
