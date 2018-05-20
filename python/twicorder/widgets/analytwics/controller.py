#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from collections import Counter
from pprint import pprint

from PyQt5 import QtCore, QtWidgets

from twicorder.widgets.analytwics.model import Model
from twicorder.widgets.analytwics.view import View


class AnalyTwics(QtCore.QObject):

    def __init__(self, parent=None):
        super(AnalyTwics, self).__init__(parent=parent)

        self.model = Model()
        self.view = View()

        self.model.tweet_loaded.connect(self.on_tweet_loaded)
        self.model.start_file.connect(self.on_start_file)
        self.model.loading_complete.connect(self.on_loading_complete)
        self.model.loading_started.connect(self.on_loading_started)

        self.__file_count = 0
        self.__tweet_count = 0
        self.__file_number = 0

        self.model.load_tweets()

    def on_tweet_loaded(self):
        self.__tweet_count += 1
        self.view.tweet_count = self.__tweet_count

    def on_start_file(self, number):
        self.__file_number = number
        progress = number / float(self.__file_count) * 100
        self.view.progress_value = progress
        self.view.progress_label = (
            f'{progress:.0f}% ({number}/{self.__file_count})'
        )

    def on_loading_complete(self):
        self.view.progress.hide()
        self.view._progress_label.hide()
        users = []
        hashtags = []
        followers_count = {}
        for tweet in self.model.tweets:
            user = tweet.json_data.get('user')
            if user:
                handle = user.get('screen_name')
                users.append(handle)
                followers_count[handle] = max(followers_count.get(handle, 0), user['followers_count'])
            for tag in tweet.json_data.get('entities', {}).get('hashtags', []):
                hashtags.append(tag['text'])
        self.view.set_top_tweeters(Counter(users))
        self.view.set_top_hashtags(Counter(hashtags))
        self.view.set_most_followed(followers_count)

    def on_loading_started(self, file_count):
        self.__file_count = file_count
        self.view.progress_value = 0

    def show(self):
        self.view.show()

    def close(self):
        self.view.close()

    def exit(self, code):
        self.view.exit(code)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = AnalyTwics()
    win.show()
    sys.exit(app.exec_())
