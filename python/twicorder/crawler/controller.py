#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time

import tweepy

from datetime import datetime

from twicorder.auth import get_auth_handler
from twicorder.config import Config
from twicorder.utils import write, message


def limit_handler(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15 * 60)


def main():
    auth = get_auth_handler()
    api = tweepy.API(auth)

    config = Config.get()

    save_path = ''
    save_path_pattern = (
        '{save_dir}/crawler/slpng_giants_timeline/{timestamp}{save_postfix}'
    )

    account_id = '799047255378391040'
    tweets = []
    total_tweets = 0
    start = datetime.now()
    for status in limit_handler(tweepy.Cursor(api.user_timeline, user_id=account_id, include_rts=True, max_id='976825230281732096').items()):
        if not save_path or len(tweets) >= config['tweets_per_file']:
            tweets = []
            timestamp = '{:%Y-%m-%d_%H-%M-%S.%f}'.format(datetime.now())
            save_path = save_path_pattern.format(timestamp=timestamp, **config)
            save_path = os.path.expanduser(save_path)
            save_dir = os.path.dirname(save_path)
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir, exist_ok=True)
        total_tweets += 1
        tweets.append(status._json)
        write(json.dumps(status._json) + '\n', save_path)
        timestamp = '{:%d %b %Y %H:%M:%S}'.format(datetime.now())
        tweet = status._json['text']
        if not tweet:
            continue
        user = status._json.get('user', {}).get('screen_name', '-')
        print(u'{}, @{}: {}'.format(timestamp, user, tweet.replace('\n', ' ')))
    end = datetime.now()
    msg = 'Finished crawling {} tweets in {}.'
    message('Info', msg.format(total_tweets, end - start))


if __name__ == '__main__':
    main()
