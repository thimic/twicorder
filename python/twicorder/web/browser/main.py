#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re

from datetime import datetime

from flask import Flask, render_template, abort
from flask_bootstrap import Bootstrap

from twicorder.config import Config
from twicorder.constants import TW_TIME_FORMAT
from twicorder.utils import readlines


app = Flask(__name__)
bootstrap = Bootstrap(app)


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return '{:3.1f}{}{}'.format(num, unit, suffix)
        num /= 1024.0
    return '{:3.1f}{}{}'.format(num, 'Yi', suffix)


def urlize(text):
    handle_pattern = re.compile(r'@(\w+)')
    text = handle_pattern.sub(
        '<a href="https://twitter.com/\g<1>" target="blank">\g<0></a>', text
    )
    hashtag_pattern = re.compile(r'#(\w+)')
    text = hashtag_pattern.sub(
        '<a href="https://twitter.com/hashtag/\g<1>" target="blank">\g<0></a>', text
    )
    return text


def format_tweet(tweet_data):
    if tweet_data.get('created_at'):
        tweet_data['created_at'] = datetime.strptime(
            tweet_data['created_at'], TW_TIME_FORMAT
        )
    if tweet_data.get('text'):
        tweet_data['text'] = urlize(tweet_data['text'])
    if tweet_data.get('full_text'):
        tweet_data['full_text'] = urlize(tweet_data['full_text'])
    return tweet_data


@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def index(req_path):
    base_dir = Config.get()['save_dir']

    # Joining the base and the requested path
    abs_path = os.path.expanduser(os.path.join(base_dir, req_path))

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        tweets = [json.loads(l) for l in readlines(abs_path)]

        # Filter out lines not containing tweets, such as delete messages.
        tweets = [t for t in tweets if t.get('id')]

        for t in tweets:
            format_tweet(t)

        return render_template(
            'tweets.html',
            endpoint=os.path.dirname(req_path),
            tweets=tweets
        )

    # Show directory contents
    files = {
        p: {
            'size': sizeof_fmt(os.path.getsize(os.path.join(abs_path, p))),
            'timestamp': datetime.fromtimestamp(
                os.path.getmtime(os.path.join(abs_path, p))
            ),
            'icon': (
                'glyphicon glyphicon-file' if
                os.path.isfile(os.path.join(abs_path, p)) else
                'glyphicon glyphicon-folder-open'
            )
        }
        for p in sorted(os.listdir(abs_path)) if not p.startswith('.')
    }
    return render_template('files.html', files=files, path=req_path)


if __name__ == '__main__':
    app.run('localhost')

