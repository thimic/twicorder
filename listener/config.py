
import datetime
import os
import yaml

from constants import THIS_DIR


class Config(object):

    _cache = None
    _cache_time = None

    @staticmethod
    def _load():
        with open(os.path.join(THIS_DIR, 'config.yaml'), 'r') as stream:
            config = yaml.load(stream)
        return config

    @classmethod
    def get(cls):
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
