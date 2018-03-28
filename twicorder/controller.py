#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time

from datetime import datetime, timedelta, timezone

from tweepy import Stream
from tweepy.api import API
from tweepy.streaming import StreamListener

from twicorder import utils
from twicorder.auth import get_auth_handler
from twicorder.config import Config
from twicorder.constants import TW_TIME_FORMAT


class TwicorderListener(StreamListener):

    def __init__(self, auth=None, api=None):
        self.api = api or API(auth)
        self._config = Config()
        self._data = []
        self._users = {}
        self._file_name = None

    @property
    def config(self):
        return self._config.get()

    @property
    def users(self):
        this_tz = datetime.now(timezone.utc).astimezone().tzinfo
        cull_time = timedelta(
            minutes=self.config.get('user_lookup_interval', 15)
        )
        now = datetime.now()
        now_local = now.astimezone(this_tz)
        to_pop = []
        for handle, user in self._users.items():
            timestamp = datetime.strptime(user['recorded_at'], TW_TIME_FORMAT)
            if now_local - timestamp > cull_time:
                to_pop.append(handle)
        for pop in to_pop:
            self._users.pop(pop)
        return self._users

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
    def file_name(self):
        if not self._file_name or len(self._data) >= self.tweets_per_file:
            self._data = []
            now = '{:%Y-%m-%d_%H-%M-%S.%f}'.format(datetime.now())
            self._file_name = self.save_prefix + now + self.save_postfix
        return self._file_name

    @staticmethod
    def extract_extended(data):
        return data.get('extended_tweet', {}).get('full_text')

    @classmethod
    def get_full_text(cls, data):
        for d in [data, data.get('retweeted_status', {})]:
            text = cls.extract_extended(d)
            if text:
                return text
        if not data.get('text'):
            return
        return data['text']

    def update_mentions(self, data, created_at=None):
        if not created_at:
            created_at = data['created_at']
        for key in data:
            if key == 'user_mentions':
                for mention in data[key]:
                    user_id = mention['id_str']
                    if user_id not in self.users:
                        user_json = self.api.get_user(mention['id_str'])._json
                        user_json['recorded_at'] = created_at
                        self.users[user_json['id_str']] = user_json
                    mention.update(self.users[user_id])
            elif isinstance(data[key], dict):
                self.update_mentions(data[key], created_at)

    def on_data(self, json_data):
        file_path = os.path.join(self.save_dir, self.file_name)
        data = json.loads(json_data)
        if data.get('created_at'):
            users = utils.find_key('user', data)
            for user in users:
                user['recorded_at'] = data['created_at']
                self.users[user['id_str']] = user
            if self.config.get('full_user_mentions', False):
                self.update_mentions(data)
        self._data.append(data)
        with open(file_path, 'a') as stream:
            stream.write(json.dumps(data) + '\n')
        timestamp = '{:%d %b %Y %H:%M:%S}'.format(datetime.now())
        tweet = self.get_full_text(data)
        if not tweet:
            utils.message('Odd Tweet!', json_data)
            return True
        print(u'{}: {}'.format(timestamp, tweet.replace('\n', ' ')))
        return True

    def on_error(self, status_code):
        message = 'Twitter error code: {}'.format(status_code)
        if status_code == 420:
            message = "Rate limitation in effect. Pausing for 5 seconds..."
            utils.message(body=message)
            time.sleep(5)
            return True
        utils.message(body=message)
        return True


class TwicorderStream(Stream):

    def __init__(self, auth, listener, **options):
        super(TwicorderStream, self).__init__(auth, listener, **options)
        self.api = API(auth)
        self._config = Config()
        self._id_to_screenname_time = None
        self._id_to_screenname = {}
        self.filter(
            follow=self.follow,
            track=self.track,
            async=self.async,
            locations=self.locations,
            stall_warnings=self.stall_warnings,
            languages=self.languages,
            encoding=self.encoding,
            filter_level=self.filter_level
        )

    @property
    def config(self):
        return self._config.get()

    @property
    def id_to_screenname(self):
        now = datetime.now()
        time_since_lookup = now - (self._id_to_screenname_time or now)
        expiry = timedelta(minutes=15)
        if self._id_to_screenname and time_since_lookup <= expiry:
            return self._id_to_screenname
        for follow_id in self.follow:
            user = self.api.get_user(follow_id)
            self._id_to_screenname[follow_id] = '@{}'.format(user.screen_name)
        self._id_to_screenname_time = datetime.now()
        print(self._id_to_screenname)
        return self._id_to_screenname

    @property
    def track(self):
        track_list = [t for t in self.config.get('track') if t] or []
        if self.follow_also_tracks:
            track_list += self.id_to_screenname.values()
        print('Tracking: ', track_list)
        return track_list

    @property
    def follow(self):
        return self.config.get('follow')

    @property
    def async(self):
        return self.config.get('async', False)

    @property
    def locations(self):
        return self.config.get('locations')

    @property
    def stall_warnings(self):
        return self.config.get('stall_warnings', False)

    @property
    def languages(self):
        return self.config.get('languages')

    @property
    def encoding(self):
        return self.config.get('encoding', 'utf8')

    @property
    def filter_level(self):
        return self.config.get('filter_level')

    @property
    def follow_also_tracks(self):
        return self.config.get('follow_also_tracks', False)


if __name__ == '__main__':
    auth = get_auth_handler()
    listener = TwicorderListener(auth=auth)
    twitter_stream = TwicorderStream(auth, listener)
    twitter_stream.filter(track=['the'])
