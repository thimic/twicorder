

from PyQt5 import QtWidgets

from tweet_viewer.widgets.tweet_list.model import TweetListModel
from tweet_viewer.widgets.tweet_list.delegate import TweetListDelegate


class TweetList(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(TweetList, self).__init__(parent=parent)
        self.setModel(TweetListModel())
        self.setItemDelegate(TweetListDelegate(self))
