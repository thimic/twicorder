#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import json
import os

from twicorder.config import Config
from twicorder.utils import read


class TwiFile(object):
    def __init__(self, path):
        self.__path = path
        self.__name = os.path.basename(path)
        self.__label = os.path.splitext(self.__name)[0]
        self.__ext = os.path.splitext(self.__name)[-1].strip('.')
        self.__data = []

    def __lt__(self, other):
        return self.name < other.name
        return os.path.getctime(self.__path) < os.path.getctime(other.__path)

    def __str__(self):
        return 'TwiFile <"{}">'.format(self.__name)

    @property
    def path(self):
        return self.__path

    @property
    def name(self):
        return self.__name

    @property
    def label(self):
        return self.__label

    @property
    def ext(self):
        return self.__ext

    @property
    def data(self):
        if not self.__data:
            for line in read(self.__path).splitlines():
                self.__data.append(json.loads(line))
        return self.__data


class TwiModel(object):
    def __init__(self):
        self._config = Config.get()
        self._location = None
        self._files = set()
        self._glob_pattern = os.path.join(
            self.location, '{}*'.format(self._config.get('save_prefix'))
        )
        self._glob_pattern = os.path.join(
            self.location, '*{}'.format(self._config.get('save_postfix'))
        )

    def refresh(self):
        self._files = set()

    @property
    def location(self):
        if not self._location:
            # self._location = os.path.expanduser(self._config.get('save_dir'))
            self._location = os.path.expanduser(os.path.join(self._config.get('save_dir'), 'slpng_giants', 'timeline'))
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def files(self):
        if not self._files:
            for path in glob.glob(self._glob_pattern):
                twifile = TwiFile(path)
                self._files.add(twifile)
        return sorted(self._files)
