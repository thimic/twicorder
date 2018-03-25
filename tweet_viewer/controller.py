
import sys

from PyQt5 import QtWidgets, QtCore

from tweet_viewer.model import TweepyModel
from tweet_viewer.view import TweepyView


class TweetViewer(QtCore.QObject):

    def __init__(self, parent=None):
        super(TweetViewer, self).__init__(parent=parent)
        self.model = TweepyModel()
        self.view = TweepyView()

        self.switchboard()

        self.populate_list()

    def switchboard(self):
        pass

    def close(self):
        self.view.close()

    def populate_list(self, limit=25):
        for idx in range(limit):
            self.view.add_tweet(next(self.model.data))

    def show(self):
        self.view.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = TweetViewer()
    win.show()
    sys.exit(app.exec_())
