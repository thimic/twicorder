
import inspect
import os

from datetime import datetime, timezone

from PyQt5 import QtWidgets, QtGui, QtCore, uic

from tweet_viewer.constants import TW_TIME_FORMAT

THIS_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))

form, wid = uic.loadUiType(os.path.join(THIS_DIR, 'ui', 'tweetlist.ui'))


class Widget(form, wid):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent=parent)
        self.setupUi(self)


class TweetListDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(TweetListDelegate, self).__init__(parent=parent)
        # widget_path = os.path.join(THIS_DIR, 'ui', 'tweetlist.ui')
        # self.widget = uic.loadUi(widget_path)
        self.widget = Widget()

    def update_widget(self, option, index):
        tweet = index.data()
        handle = '@{}'.format(tweet['user']['screen_name'])
        this_tz = datetime.now(timezone.utc).astimezone().tzinfo
        timestamp = datetime.strptime(tweet['created_at'], TW_TIME_FORMAT)
        timestamp_local = timestamp.astimezone(this_tz)
        full_text = tweet.get('extended_tweet', {}).get('full_text')
        self.widget.name_label.setText(tweet['user']['name'])
        self.widget.handle_label.setText(handle)
        self.widget.tweet_label.setText(full_text or tweet['text'])
        self.widget.time_label.setText('{:%a %-d %b %H:%M}'.format(timestamp_local))
        self.widget.avatar_label.setPixmap(tweet['user']['avatar'])
        self.widget.resize(self.sizeHint(option, index))
        palette = self.widget.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(252, 252, 252))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 0))
        if option.state & QtWidgets.QStyle.State_Selected:
            palette.setColor(QtGui.QPalette.Window, palette.color(QtGui.QPalette.Highlight))
            palette.setColor(QtGui.QPalette.WindowText, palette.color(QtGui.QPalette.BrightText))
        self.widget.setPalette(palette)

    def paint(self, painter, option, index):
        self.update_widget(option, index)
        painter.save()
        self.widget.render(
            painter,
            targetOffset=option.rect.topLeft(),
            sourceRegion=QtGui.QRegion(self.widget.rect())
        )
        pen = QtGui.QPen(QtGui.QColor(230, 230, 230))
        painter.setPen(pen)
        painter.drawLine(option.rect.topLeft(), option.rect.topRight())
        painter.restore()

    def createEditor(self, parent, option, index):
        print('Editor!')
        self.update_widget(option, index)
        return self.widget

    def sizeHint(self, option, index):
        self.widget.resize(option.rect.width(), 0)
        self.widget.adjustSize()
        return QtCore.QSize(option.rect.width(), self.widget.height())
