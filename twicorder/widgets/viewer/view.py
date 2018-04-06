#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import json
import os
import sys

from PyQt5 import QtCore, QtWidgets, uic

from twicorder.constants import APP, COMPANY


THIS_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
form_class, base_class = uic.loadUiType(os.path.join(THIS_DIR, 'ui', 'mainwindow.ui'))


class TwiFileItem(QtWidgets.QListWidgetItem):

    def __init__(self, twifile, parent=None):
        super(TwiFileItem, self).__init__(parent=parent)
        self.__twifile = twifile
        self.setText(twifile.name)

    @property
    def twifile(self):
        return self.__twifile


class TwiTweetItem(QtWidgets.QListWidgetItem):

    def __init__(self, tweet, parent=None):
        super(TwiTweetItem, self).__init__(parent=parent)
        self.__tweet = tweet
        self.setText(tweet.get('id_str'))

    @property
    def tweet(self):
        return self.__tweet


class TwiView(form_class, base_class):

    def __init__(self, parent=None):
        super(TwiView, self).__init__(parent=parent)
        self.setupUi(self)

        self.statusbar_label = QtWidgets.QLabel()
        self.statusBar().addWidget(self.statusbar_label)

        self.restore_window_state()

    def closeEvent(self, event):
        settings = QtCore.QSettings(COMPANY, APP)
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('window_state', self.saveState())
        super(TwiView, self).closeEvent(event)

    def restore_window_state(self):
        settings = QtCore.QSettings(COMPANY, APP)
        geometry = settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        window_state = settings.value('window_state')
        if window_state:
            self.restoreState(window_state)

    @property
    def status_label(self):
        return self.statusbar_label.text()

    @status_label.setter
    def status_label(self, value):
        self.statusbar_label.setText(value)

    @property
    def location(self):
        return self.location_lineedit.text()

    @location.setter
    def location(self, location):
        self.location_lineedit.setText(location)

    def add_files(self, twifiles):
        self.files_listwidget.clear()
        self.status_label = 'Files: {}'.format(len(twifiles))
        for twifile in twifiles:
            item = TwiFileItem(twifile)
            self.files_listwidget.addItem(item)

    def add_tweets(self, tweets):
        self.tweets_listwidget.clear()
        for tweet in tweets:
            item = TwiTweetItem(tweet)
            self.tweets_listwidget.addItem(item)

    def add_data(self, data):
        self.data_treewidget.clear()
        root = self.data_treewidget.topLevelItem(0)
        self.build_tree(data, root)
        self.data_treewidget.resizeColumnToContents(0)
        self.data_textedit.setPlainText(json.dumps(data))

    def build_tree(self, data, root, index=0):
        if isinstance(data, dict):
            for k, v in data.items():
                item = QtWidgets.QTreeWidgetItem(root)
                item.setText(index, k)
                self.data_treewidget.insertTopLevelItem(index, item)
                if isinstance(v, (str, int, float, bool)) or v is None:
                    item.setText(index + 1, repr(v))
                    continue

                self.build_tree(v, item, index)
        elif isinstance(data, (str, int, float, bool)) or data is None:
            item = QtWidgets.QTreeWidgetItem(root)
            item.setText(index, repr(data))
        elif isinstance(data, (list, tuple)):
            for idx, i in enumerate(data):
                if isinstance(i, dict):
                    item = QtWidgets.QTreeWidgetItem(root)
                    item.setText(index, '<item {}>'.format(idx + 1))
                    self.build_tree(i, item, index)
                    continue
                self.build_tree(i, root, index + 1)

    @property
    def files(self):
        return self.files_listwidget.items()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = TwiView()
    win.show()
    sys.exit(app.exec_())
