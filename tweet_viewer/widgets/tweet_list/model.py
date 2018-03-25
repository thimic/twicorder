
from PyQt5 import QtCore


class TweetListModel(QtCore.QAbstractListModel):
    def __init__(self, tweets=None, parent=None):
        """ datain: a list where each item is a row
        """
        super(TweetListModel, self).__init__(parent)
        self.tweets = tweets or []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.tweets)

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            tweet = self.tweets[index.row()]
            return tweet
            full_text = tweet.get('extended_tweet', {}).get('full_text')
            return full_text or tweet['text']

    def addItem(self, item):
        self.tweets.append(item)

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
