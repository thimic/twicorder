
from PyQt5 import QtWidgets, QtCore

from tweet_viewer.widgets.tweet_list.widget import TweetList


class TweepyView(QtWidgets.QMainWindow):

    closed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TweepyView, self).__init__(parent=parent)
        self.setWindowTitle('TweepyViewer')
        self.resize(500, 900)
        self.tweet_list = TweetList()
        self.setCentralWidget(self.tweet_list)

    def add_tweet(self, tweet):
        self.tweet_list.model().addItem(tweet)

    def closeEvent(self, event):
        self.closed.emit()
        super(TweepyView, self).closeEvent(event)
