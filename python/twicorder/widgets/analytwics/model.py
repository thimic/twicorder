#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import json
import os


from PyQt5 import QtCore

from twicorder.config import Config
from twicorder.utils import readlines


class TweetLoader(QtCore.QThread):

    tweet_loaded = QtCore.pyqtSignal(dict)
    start_file = QtCore.pyqtSignal(int)
    loading_started = QtCore.pyqtSignal(int)
    loading_complete = QtCore.pyqtSignal()

    def run(self):
        config = Config.get()
        tweet_dir = os.path.expanduser(config.get('save_dir'))
        prefix = config.get('save_prefix')
        glob_pattern = '{}*'.format(os.path.join(tweet_dir, prefix))
        glob_pattern = os.path.expanduser('~/Desktop/slpng_giants*.txt')
        print(glob_pattern)
        paths = glob.glob(glob_pattern)
        self.loading_started.emit(len(paths))
        for idx, path in enumerate(paths):
            self.start_file.emit(idx + 1)
            for line in readlines(path):
                try:
                    self.tweet_loaded.emit(json.loads(line))
                except Exception:
                    print(line)
        self.loading_complete.emit()


class Tweet(object):
    def __init__(self, json_data):
        self.__json_data = json_data

    @property
    def json_data(self):
        return self.__json_data


class Model(QtCore.QObject):

    tweet_loaded = QtCore.pyqtSignal()
    start_file = QtCore.pyqtSignal(int)
    loading_started = QtCore.pyqtSignal(int)
    loading_complete = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Model, self).__init__(parent=parent)
        self.__config = Config.get()
        self.__tweets = []
        self.__tweet_loader = TweetLoader()
        
    @property
    def tweets(self):
        return self.__tweets

    @property
    def config(self):
        return self.__config.copy()
    
    def load_tweets(self):
        self.__tweet_loader.tweet_loaded.connect(self.on_tweet_loaded)
        self.__tweet_loader.start_file.connect(self.start_file.emit)
        self.__tweet_loader.loading_started.connect(self.loading_started.emit)
        self.__tweet_loader.loading_complete.connect(self.loading_complete.emit)
        self.__tweet_loader.start()

    def on_tweet_loaded(self, tweet):
        self.__tweets.append(Tweet(tweet))
        self.tweet_loaded.emit()
