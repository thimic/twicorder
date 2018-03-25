

from tweet_viewer.constants import TWEET_DIRS, Ascending, Decending
from tweet_viewer.reader.tweepy_reader import TweepyReader
from tweet_viewer.utils import load_avatar


class TweepyModel(object):

    def __init__(self):
        self._data = []
        self._max_index = 0
        self._reader = TweepyReader(TWEET_DIRS)
        self._generator = self._reader.read(self.sort_key, self.sort_order)

    @property
    def data(self):
        for item in self._generator:
            avatar = load_avatar(item['user']['profile_image_url_https'])
            item['user']['avatar'] = avatar
            self._data.append(item)
            print(item)
            yield item

    @property
    def sort_order(self):
        return Decending

    @property
    def sort_key(self):
        return 'mtime'

    def update(self):
        self._data = []
        self._max_index = 0
        self._generator = self._reader.read(self.sort_key, self.sort_order)
