
import datetime
import os

import yaml

from tweepy import Stream
from tweepy.streaming import StreamListener

from auth import get_auth_handler
from constants import THIS_DIR


class TwitterListener(StreamListener):

    def __init__(self, *args, **kwargs):
        super(TwitterListener, self).__init__(*args, **kwargs)
        self._auth = get_auth_handler()
        self._config = None
        self._config_time = None
        self._data = []
        self._file_name = None

    @staticmethod
    def load_config():
        with open(os.path.join(THIS_DIR, 'config.yaml'), 'r') as stream:
            config = yaml.load(stream)
        return config

    @property
    def config(self):
        if not self._config:
            self._config = self.load_config()
            self._config_time = datetime.datetime.now()
            return self._config
        interval = datetime.timedelta(
            seconds=self._config['config_reload_interval']
        )
        if datetime.datetime.now() - self._config_time > interval:
            self._config = self.load_config()
            self._config_time = datetime.datetime.now()
            print 'config reload!'
        return self._config

    @property
    def auth(self):
        return self._auth

    @property
    def keywords(self):
        return self.config['keywords']

    @property
    def follow(self):
        return self.config['follow']

    @property
    def save_dir(self):
        return os.path.expanduser(self.config['save_dir'])

    @property
    def save_prefix(self):
        return self.config['save_prefix']

    @property
    def save_postfix(self):
        return self.config['save_postfix']

    @property
    def tweets_per_file(self):
        return self.config['tweets_per_file']

    @property
    def config_reload_interval(self):
        return self.config['config_reload_interval']

    @property
    def file_name(self):
        if not self._file_name or len(self._data) >= self.tweets_per_file:
            self._data = []
            now = '{:%Y-%m-%d_%H-%M-%S.%f}'.format(datetime.datetime.now())
            self._file_name = self.save_prefix + now + self.save_postfix
        return self._file_name

    def on_data(self, data):
        self._data.append(data)
        file_path = os.path.join(self.save_dir, self.file_name)
        with open(file_path, 'a') as stream:
            stream.write(data)
        return True

    def on_error(self, status):
        print(status)
        return True


if __name__ == '__main__':
    listener = TwitterListener()
    twitter_stream = Stream(listener.auth, listener)
    twitter_stream.filter(track=listener.keywords, follow=listener.follow)
