#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect

from threading import Thread

from twicorder.search.exchange import QueryExchange
from twicorder.search.tasks import TaskManager
from twicorder.search.queries import RequestQuery
from twicorder.search.queries import request_queries


class WorkerThread(Thread):

    def setup(self, func, tasks, query_exchange):
        self._running = False
        self._func = func
        self._tasks = tasks
        self._query_exchange = query_exchange

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            for task in self._tasks:
                if not task.due:
                    continue
                self._query_exchange.add(self._func(task))


class Scheduler(object):

    def __init__(self):
        self._task_manager = TaskManager()
        self._query_exchange = QueryExchange()
        self._worker_thread = WorkerThread()
        self._query_types = {}

    @property
    def task_manager(self):
        return self._task_manager

    @property
    def tasks(self):
        return self._task_manager.tasks

    @property
    def query_exchange(self):
        return self._query_exchange

    @property
    def query_types(self):
        if self._query_types:
            return self._query_types
        for name, item in inspect.getmembers(request_queries, inspect.isclass):
            if item == RequestQuery:
                continue
            elif issubclass(item, RequestQuery):
                self._query_types[item._name] = item
        return self._query_types

    def stop(self):
        self._worker_thread.stop()

    def run(self):
        self._worker_thread.setup(
            func=self.cast_query,
            tasks=self.tasks,
            query_exchange=self.query_exchange
        )
        self._worker_thread.start()

    def cast_query(self, task):
        query_object = self.query_types[task.name]
        query = query_object(task.output, **task.kwargs)
        return query


if __name__ == '__main__':
    scheduler = Scheduler()
    scheduler.run()
