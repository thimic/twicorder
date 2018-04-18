#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import os

from PyQt5 import QtWidgets, QtCore, uic


THIS_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
form_class, base_class = uic.loadUiType(os.path.join(THIS_DIR, 'ui', 'view.ui'))


class DigitItem(QtWidgets.QTableWidgetItem):
    def __init__(self, value):
        super(DigitItem, self).__init__(str(value))
        self.setData(QtCore.Qt.EditRole, value)

    def __lt__(self, other):
        if isinstance(other, DigitItem):
            self_val = int(self.data(QtCore.Qt.EditRole))
            other_val = int(other.data(QtCore.Qt.EditRole))
            return self_val < other_val
        return super(DigitItem, self).__lt__(other)


class View(form_class, base_class):

    def __init__(self, parent=None):
        super(View, self).__init__(parent=parent)

        self.setupUi(self)

        self.progress = QtWidgets.QProgressBar()
        self._progress_label = QtWidgets.QLabel()
        self._tweet_count_label = QtWidgets.QLabel('Tweets: 0')
        self._tweet_count_label.setMinimumWidth(120)
        self._tweet_count_label.setAlignment(QtCore.Qt.AlignRight)
        self.progress.setValue(0)
        self.progress.setFixedWidth(200)
        self._progress_label.setText('0%')
        self.statusBar().addPermanentWidget(self._tweet_count_label)
        self.statusBar().addWidget(self.progress)
        self.statusBar().addWidget(self._progress_label)

    @property
    def progress_value(self):
        return self.progress.value()

    @progress_value.setter
    def progress_value(self, value):
        self.progress.setValue(value)

    @property
    def tweet_count(self):
        return self._tweet_count_label.text()

    @tweet_count.setter
    def tweet_count(self, value):
        self._tweet_count_label.setText(f'Tweets: {value}')

    @property
    def progress_label(self):
        return self._progress_label.text()

    @progress_label.setter
    def progress_label(self, value):
        self._progress_label.setText(value)

    def set_top_tweeters(self, counter):
        # self.top_tweeters_table.clear()
        self.top_tweeters_table.setColumnCount(2)
        self.top_tweeters_table.setRowCount(len(counter))
        for idx, (user, count) in enumerate(sorted(counter.items(), key=lambda x: x[1], reverse=True)):
            user_item = QtWidgets.QTableWidgetItem(f'@{user}')
            count_item = DigitItem(count)
            self.top_tweeters_table.setItem(idx, 0, user_item)
            self.top_tweeters_table.setItem(idx, 1, count_item)
        self.top_tweeters_table.resizeColumnToContents(0)

    def set_top_hashtags(self, counter):
        # self.top_tweeters_table.clear()
        self.top_hashtags_table.setColumnCount(2)
        self.top_hashtags_table.setRowCount(len(counter))
        for idx, (hashtag, count) in enumerate(sorted(counter.items(), key=lambda x: x[1], reverse=True)):
            user_item = QtWidgets.QTableWidgetItem(f'#{hashtag}')
            count_item = DigitItem(count)
            self.top_hashtags_table.setItem(idx, 0, user_item)
            self.top_hashtags_table.setItem(idx, 1, count_item)
        self.top_hashtags_table.resizeColumnToContents(0)

    def set_most_followed(self, counter):
        # self.top_tweeters_table.clear()
        self.most_followed_table.setColumnCount(2)
        self.most_followed_table.setRowCount(len(counter))
        for idx, (user, count) in enumerate(sorted(counter.items(), key=lambda x: x[1], reverse=True)):
            user_item = QtWidgets.QTableWidgetItem(f'@{user}')
            count_item = DigitItem(count)
            self.most_followed_table.setItem(idx, 0, user_item)
            self.most_followed_table.setItem(idx, 1, count_item)
        self.most_followed_table.resizeColumnToContents(0)
