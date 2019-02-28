#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time
import copy

from datetime import datetime, timedelta, timezone

from tweepy import Stream
from tweepy.api import API
from tweepy.streaming import StreamListener

from twicorder import mongo
from twicorder import utils
from twicorder.auth import get_auth_handler
from twicorder.config import Config
from twicorder.constants import TW_TIME_FORMAT

logger = utils.FileLogger.get()


class TwicorderListener(StreamListener):

    def __init__(self, auth=None, api=None):
        """
        TwicorderListener constructor.

        Args:
            auth (tweepy.OAuthHandler): Authentication handler
            api (tweepy.api.API): Tweepy API instance

        """
        self.api = api or API(auth)
        self._config = Config()
        self._data = []
        self._users = {}
        self._file_name = None
        self._mongo_collection = None

    @property
    def config(self):
        """
        Object holding the user config.

        Returns:
            dict: Config object

        """
        return self._config.get()

    @property
    def users(self):
        """
        Holds a list of captured user data that has not expired. Expiry time
        can be set in the config file and defaults to 15 minutes.

        Returns:
            dict: Users (id_str: user dict)

        """
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
        """
        Save location for captured data. Set in config file.

        Returns:
            str: Path to save location for captured data

        """
        save_dir = os.path.expanduser(
            os.path.join(self.config['save_dir'], 'stream')
        )
        return save_dir

    @property
    def save_prefix(self):
        """
        Names of files containing captured data will be prefixed with this
        string. Set in config file.

        Returns:
            str: Prefix

        """
        return self.config['save_prefix']

    @property
    def save_postfix(self):
        """
        Names of files containing captured data will be postfixed with this
        string. Set in config file.

        Returns:
            str: Postfix. Often extension, such as ".txt"

        """
        return self.config['save_postfix']

    @property
    def tweets_per_file(self):
        """
        Max number of tweets saved to one file. Set in config file.

        Returns:
            int: Max number of tweets

        """
        return self.config['tweets_per_file']

    @property
    def file_name(self):
        """
        Generates the file name used when saving captured data.

        Returns:
            str: File name

        """
        if not self._file_name or len(self._data) >= self.tweets_per_file:
            self._data = []
            now = '{:%Y-%m-%d_%H-%M-%S.%f}'.format(datetime.now())
            self._file_name = self.save_prefix + now + self.save_postfix
        return self._file_name

    @property
    def mongo_collection(self):
        """
        MongoDB collection to record tweets in.

        Returns:
            pymongo.Collection: MongoDB collection

        """
        if not self._mongo_collection or not mongo.is_connected(self._mongo_collection):
            self._mongo_collection = mongo.create_collection()
        return self._mongo_collection

    @staticmethod
    def extract_extended(data):
        """
        Extracts the full text tweet from a tweet object if available.

        Args:
            data (dict): Tweet object

        Returns:
            str: Tweet text

        """
        return data.get('extended_tweet', {}).get('full_text')

    @classmethod
    def get_full_text(cls, data):
        """
        Gets the full text for the given tweet, whether it is an extended tweet
        or not.

        Args:
            data (dict): Tweet object

        Returns:
            Tweet text

        """
        for d in [data, data.get('retweeted_status', {})]:
            text = cls.extract_extended(d)
            if text:
                return text
        if not data.get('text'):
            return
        return data['text']

    def update_mentions(self, data, created_at=None):
        """
        Fleshing out the mentions section of a tweet object with full user
        information, rather than just a stub. Utilises cached user data if
        available. Otherwise querying the API for user data.

        Args:
            data (dict): Tweet object
            created_at (str): Tweet timestamp

        """
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
        """
        Defines the actions to take on data capture. Caching all available user
        data and writing tweet data to disk.

        Args:
            json_data (str): String containing tweet data on JSON format

        Returns:
            bool: True if successful

        """
        file_path = os.path.join(self.save_dir, self.file_name)
        data = json.loads(json_data)
        if data.get('created_at'):
            users = utils.collect_key_values('user', data)
            for user in users:
                user['recorded_at'] = data['created_at']
                self.users[user['id_str']] = user
            if self.config.get('full_user_mentions', False):
                self.update_mentions(data)

            # Add tweet to MongoDB
            if self.config.get('use_mongo') or True and self.mongo_collection:
                try:
                    mongo_data = copy.deepcopy(data)
                    mongo_data = utils.timestamp_to_datetime(mongo_data)
                    mongo_data = utils.stream_to_search(mongo_data)
                    self.mongo_collection.replace_one(
                        {'id': mongo_data['id']},
                        mongo_data,
                        upsert=True
                    )
                except Exception:
                    logger.exception(
                        'Twicorder Listener: Unable to connect to MongoDB: '
                    )

        self._data.append(data)
        utils.write(json.dumps(data) + '\n', file_path)
        timestamp = '{:%d %b %Y %H:%M:%S}'.format(datetime.now())
        tweet = self.get_full_text(data)
        if not tweet:
            return True
        user = data.get('user', {}).get('screen_name', '-')
        print(u'{}, @{}: {}'.format(timestamp, user, tweet.replace('\n', ' ')))
        return True

    def on_error(self, status_code):
        """
        Defines the actions to take when errors are encountered. Printing
        warnings. If error code 420 is encountered, Twitter's rate limit has
        been exceeded and Twicorder will pause for 5 seconds before resuming
        operation.

        Args:
            status_code (int): Twitter API error code

        Returns:
            bool: True if error is not critical

        """
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
        msg = 'Listener starting at {:%d %b %Y %H:%M:%S}'.format(datetime.now())
        utils.message('Info', msg)
        self.api = API(auth)
        self._config = Config()
        self._id_to_screenname_time = None
        self._id_to_screenname = {}
        stream_mode = self.config.get('stream_mode') or 'filter'
        if stream_mode == 'filter':
            self.filter(
                follow=self.follow,
                track=self.track,
                locations=self.locations,
                stall_warnings=self.stall_warnings,
                languages=self.languages,
                encoding=self.encoding,
                filter_level=self.filter_level
            )
        elif stream_mode == 'sample':
            self.sample(
                languages=self.languages,
                stall_warnings=self.stall_warnings
            )
        else:
            utils.message('Error', 'stream_mode must be "filter" or "sample"')

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
        track_list = [t for t in self.config.get('track') or [] if t] or None
        if track_list and self.follow_also_tracks:
            track_list += self.id_to_screenname.values()
        print('Tracking: ', track_list)
        return track_list

    @property
    def follow(self):
        return self.config.get('follow')

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
