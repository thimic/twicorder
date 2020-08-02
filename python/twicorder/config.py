#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import yaml

from typing import Optional


class Config(object):
    """
    Class for reading config file. Re-checking file on disk after a set
    interval to pick up changes.
    """

    _cache = None
    _cache_time = None
    _config_dir = None
    _project_dir = None

    @classmethod
    def setup(cls, project_dir: str, config_dir: Optional[str] = None):
        """
        Set up Config class with the given file paths. Config defaults to the
        project dir, but can also be specified separately.

        Args:
            project_dir: Project directory
            config_dir: Config file directory

        """
        cls._config_dir = config_dir or project_dir
        cls._project_dir = project_dir

    @classmethod
    def _load(cls):
        """
        Reading config file from disk and parsing to a dictionary using the
        yaml module.

        Returns:
            dict: Config object

        """
        listener_path = os.path.join(cls._config_dir, 'config.yaml')
        with open(listener_path, 'r') as stream:
            config = yaml.safe_load(stream)
        config['project_dir'] = cls._project_dir
        config['appdata_dir'] = os.path.join(cls._project_dir, 'appdata')
        config['output_dir'] = os.path.join(cls._project_dir, 'output')
        config['log_dir'] = os.path.join(cls._project_dir, 'logs')
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
