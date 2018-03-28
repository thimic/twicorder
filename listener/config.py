#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import yaml

from constants import THIS_DIR


class Config(object):
    """
    Class for reading config file. Re-checking file on disk after a set
    interval to pick up changes.
    """

    _cache = None
    _cache_time = None

    @staticmethod
    def _load():
        """
        Reading config file from disk and parsing to a dictionary using the
        yaml module.

        Returns:
            dict: Config object

        """
        listener_path = os.path.join(THIS_DIR, 'config', 'listener.yaml')
        with open(listener_path, 'r') as stream:
            config = yaml.load(stream)
        return config

    @classmethod
    def get(cls):
        """
        Reads config file from disk if no config object has been loaded or if
        the available config object has expired. Otherwise serving up a cached
        config object.

        Returns:
            dict: Config object

        """
        if not cls._cache:
            cls._cache = cls._load()
            cls._cache_time = datetime.datetime.now()
            return cls._cache
        reload_interval = cls._cache['config_reload_interval']
        max_interval = datetime.timedelta(seconds=reload_interval)
        if datetime.datetime.now() - cls._cache_time > max_interval:
            cls._cache = cls._load()
            cls._cache_time = datetime.datetime.now()
        return cls._cache
