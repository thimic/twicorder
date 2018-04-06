#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtWidgets, QtCore

from twicorder.widgets.viewer.model import TwiModel
from twicorder.widgets.viewer.view import TwiView


class TwiViewer(QtCore.QObject):

    def __init__(self, parent=None):
        super(TwiViewer, self).__init__(parent=parent)

        self.model = TwiModel()
        self.view = TwiView()

        self.model_to_view()

        self.switchboard()

    def switchboard(self):
        self.view.files_listwidget.currentItemChanged.connect(self.on_file_selected)
        self.view.tweets_listwidget.currentItemChanged.connect(self.on_tweet_selected)

    def on_file_selected(self, current, previous):
        if not current:
            return
        self.view.add_tweets(current.twifile.data)
        label = (
            'Files: {}  Tweets: {}'
            .format(len(self.model.files), len(current.twifile.data))
        )
        self.view.status_label = label

    def on_tweet_selected(self, current, previous):
        if not current:
            return
        self.view.add_data(current.tweet)

    def model_to_view(self):
        self.view.location = self.model.location
        self.view.add_files(self.model.files)

    def show(self):
        self.view.show()

    def close(self):
        self.view.close()

    def exit(self, code):
        self.view.exit(code)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = TwiViewer()
    win.show()
    sys.exit(app.exec_())
