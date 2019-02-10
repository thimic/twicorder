#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import json
import os

from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker

from twicorder.constants import (
    COMPRESSED_EXTENSIONS,
    REGULAR_EXTENSIONS,
)
from twicorder.config import Config
from twicorder.exporter.tables import create_tables
from twicorder.exporter.tables import (
    Base,
    Hashtag,
    Media,
    Mention,
    Symbol,
    Tweet,
    Url,
    User,
)
from twicorder.utils import readlines, str_to_date


class Exporter:

    def __init__(self, export_path, autostart=False):
        engine = create_engine(export_path)
        create_tables(engine)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()

        if autostart:
            self.start()

    @property
    def config(self):
        return Config.get()

    def _collect_file_paths(self):
        """
        Collecting a list of all files to be ingested into database.

        Returns:
            list[str]: List of file paths

        """
        root_path = os.path.expanduser(self.config['save_dir'])
        extensions = REGULAR_EXTENSIONS + COMPRESSED_EXTENSIONS
        search_pattern = os.path.join(root_path, '**', '*.*')
        paths = glob.glob(search_pattern, recursive=True)
        paths = [
            p for p in paths if os.path.splitext(p)[-1].strip('.') in extensions
        ]
        return sorted(paths)

    def _get_tweet_type(self, tweet_obj):
        reply_status = tweet_obj.get('in_reply_to_status_id')
        reply_user = tweet_obj.get('in_reply_to_user_id')
        retweet = tweet_obj.get('retweeted_status')
        quote = tweet_obj.get('quoted_status')

        tweet_type = 'tw'
        if reply_status or reply_user:
            tweet_type = 're'
        if retweet:
            tweet_type = 'rt'
        elif quote:
            tweet_type = 'qt'
        return tweet_type

    def _get_tweet_text(self, tweet_obj):
        # Todo: Account for extended tweets from the streaming API
        text_obj = tweet_obj
        if tweet_obj.get('retweeted_status'):
            text_obj = tweet_obj['retweeted_status']
        elif tweet_obj.get('quoted_status'):
            text_obj = tweet_obj['quoted_status']
        return text_obj.get('full_text', text_obj.get('text'))

    def register_tweet(self, tweet_obj):

        (ret,), = self.session.query(exists().where(Tweet.tweet_id == tweet_obj['id']))
        if ret:
            print('Skipping duplicate')
            return

        # Register author
        author = self.register_user(tweet_obj['user'], tweet_obj['id'])

        # Register entities
        # Todo: Account for extended tweets from the streaming API
        for hashtag in tweet_obj['entities'].get('hashtags', []):
            self.register_hashtag(hashtag, tweet_obj['id'])
        for symbol in tweet_obj['entities'].get('symbols', []):
            self.register_symbol(symbol, tweet_obj['id'])
        for url in tweet_obj['entities'].get('urls', []):
            self.register_url(url, tweet_obj['id'])
        # Todo: Account for extended entities
        for media in tweet_obj['entities'].get('media', []):
            self.register_media(media, tweet_obj['id'])
        # Todo: Mentions!

        # Register tweet
        tweet = Tweet(
            tweet_id=tweet_obj['id'],
            created_at=str_to_date(tweet_obj['created_at']),
            tweet_type=self._get_tweet_type(tweet_obj),
            text=self._get_tweet_text(tweet_obj),
            user_id=author.unique_id,
            in_reply_to_status_id=tweet_obj['in_reply_to_status_id'],
            in_reply_to_user_id=tweet_obj['in_reply_to_user_id'],
            in_reply_to_screen_name=tweet_obj['in_reply_to_screen_name'],
            # Todo: Complete table
        )
        self.session.add(tweet)
        # self.session.merge(tweet)
        self.session.commit()
        return tweet

    def register_user(self, user_obj, tweet_id):
        user = User(
            user_id=user_obj['id'],
            name=user_obj['name'],
            screen_name=user_obj['screen_name'],
            location=user_obj['location'],
            description=user_obj['description'],
            url=user_obj['url'],
            protected=user_obj['protected'],
            followers_count=user_obj['followers_count'],
            friends_count=user_obj['friends_count'],
            listed_count=user_obj['listed_count'],
            favourites_count=user_obj['favourites_count'],
            created_at=str_to_date(user_obj['created_at']),
            verified=user_obj['verified'],
            statuses_count=user_obj['statuses_count'],
            lang=user_obj['lang'],
            geo_enabled=user_obj['geo_enabled'],
            contributors_enabled=user_obj['contributors_enabled'],
            withheld_in_countries=','.join(user_obj.get('withheld_in_countries', ())),
            tweet_id=tweet_id
        )
        self.session.add(user)
        self.session.commit()
        return user

    def register_hashtag(self, hashtag_obj, tweet_id):
        text = hashtag_obj['text']
        start, end = hashtag_obj['indices']
        hashtag = Hashtag(
            text=text,
            display_start=start,
            display_end=end,
            tweet_id=tweet_id
        )
        self.session.add(hashtag)
        self.session.commit()
        return hashtag

    def register_symbol(self, symbol_obj, tweet_id):
        start, end = symbol_obj['indices']
        symbol = Symbol(
            text=symbol_obj['text'],
            display_start=start,
            display_end=end,
            tweet_id=tweet_id
        )
        self.session.add(symbol)
        self.session.commit()
        return symbol

    def register_mention(self, mention_obj, unique_user_id, tweet_id):
        start, end = mention_obj['indices']
        mention = Mention(
            display_start=start,
            display_end=end,
            unique_user_id=unique_user_id,
            tweet_id=tweet_id
        )
        self.session.add(mention)
        self.session.commit()
        return mention

    def register_media(self, media_obj, tweet_id):

        (ret,), = self.session.query(exists().where(Media.media_id == media_obj['id']))
        if ret:
            print('Skipping duplicate')
            return

        start, end = media_obj['indices']
        media = Media(
            media_id=media_obj['id'],
            media_url=media_obj['media_url'],
            url=media_obj['url'],
            expanded_url=media_obj['expanded_url'],
            media_type=media_obj['type'],
            display_start=start,
            display_end=end,
            source_status_id=media_obj.get('source_status_id'),
            tweet_id=tweet_id
        )
        self.session.add(media)
        self.session.commit()
        return media

    def register_url(self, url_obj, tweet_id):
        start, end = url_obj['indices']
        url = Url(
            url=url_obj['url'],
            expanded_url=url_obj['expanded_url'],
            display_start=start,
            display_end=end,
            tweet_id=tweet_id
        )
        self.session.add(url)
        self.session.commit()
        return url

    def start(self):
        file_paths = self._collect_file_paths()
        for file_path in file_paths:
            print(file_path)
            for line in readlines(file_path):
                try:
                    data = json.loads(line)
                except Exception as error:
                    print(error)
                    continue
                if not data.get('id'):
                    # Don't bother with delete messages
                    continue
                tweet = self.register_tweet(data)


if __name__ == '__main__':
    exporter = Exporter('sqlite:////Users/thimic/Desktop/tweets.db', True)
