#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import yaml

from twicorder.constants import CONFIG_DIR


class Task(object):

    def __init__(self, name, frequency=15, multipart=True, **kwargs):
        self._name = name
        self._frequency = frequency
        self._multipart = multipart
        self._kwargs = kwargs

        self._last_run = None

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        string = (
            f'Task('
            f'name={repr(self.name)}, '
            f'frequency={repr(self.frequency)}, '
            f'multipart={self.multipart}, '
            f'kwargs={str(self.kwargs)}'
            f')'
        )
        return string

    @property
    def name(self):
        return self._name

    @property
    def frequency(self):
        return self._frequency

    @property
    def multipart(self):
        return self._multipart

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def due(self):
        if self._last_run is None:
            self._last_run = time.time()
            return True
        if time.time() - self._last_run >= self.frequency * 60:
            self._last_run = time.time()
            return True
        return False


class TaskManager(object):

    _tasks = []

    @classmethod
    def load(cls):
        """
        Reading tasks from yaml file and parsing to a dictionary.
        """
        cls._tasks = []
        tasks_list = os.path.join(CONFIG_DIR, 'tasks.yaml')
        with open(tasks_list, 'r') as stream:
            raw_tasks = yaml.load(stream)
        for query, tasks in raw_tasks.items():
            for raw_task in tasks:
                task = Task(
                    name=query,
                    frequency=raw_task.get('frequency') or 15,
                    multipart=raw_task.get('multipart') or True,
                    **raw_task.get('kwargs') or {}
                )
                cls._tasks.append(task)

    @property
    def tasks(self):
        if not self._tasks:
            self.load()
        return self._tasks


if __name__ == '__main__':
    import json
    task_collector = TaskManager()
    for task in task_collector.tasks:
        print(task)
        print(json.dumps(task.kwargs))

