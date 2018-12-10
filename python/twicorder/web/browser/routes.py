#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re

from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from subprocess import check_output
from twicorder import mongo
from twicorder.config import Config
from twicorder.constants import TW_TIME_FORMAT
from twicorder.utils import readlines, FileLogger
from twicorder.web.browser import app, db
from twicorder.web.browser.forms import LoginForm, RegistrationForm
from twicorder.web.browser.models import User
from werkzeug.urls import url_parse

logger = FileLogger.get()


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


def systemd_status(daemon):
    try:
        raw_out = check_output(['systemctl', 'is-active', daemon]).decode()
    except Exception:
        return 'N/A'
    return raw_out


def crawler_status():
    status = {
        'Backup': systemd_status('stashbox'),
        'Streaming': systemd_status('twicorder-listener'),
        'Search': systemd_status('twicorder')
    }
    return status


@app.template_filter('date_to_millis')
def date_to_millis(dt):
    """
    Converts a datetime object to the number of milliseconds since the unix
    epoch.
    """
    return int(dt.timestamp()) * 1000


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# @app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/stats')
@login_required
def stats():
    try:
        collection = mongo.create_collection()
        data = {
            'All Tweets': f'{collection.count():,}',
        }
        accounts = {
            'slpng_giants',
            'slpng_giants_be',
            'slpng_giants_bg',
            'slpng_giants_br',
            'slpng_giants_ca',
            'slpng_giants_ch',
            'slpng_giants_de',
            'slpng_giants_es',
            'slpng_giants_eu',
            'slpng_giants_fr',
            'slpng_giants_it',
            'slpng_giants_nl',
            'slpng_giants_no',
            'slpng_giants_nz',
            'slpng_giants_oz',
            'slpng_giants_se',
        }
        for account in sorted(accounts):
            data[f'@{account}'] = (
                f'{collection.find({"user.screen_name": account}).count():,}'
            )
        return render_template('stats.html', title='Stats', data=data)
    except Exception:
        logger.exception('TwiBrowser stats error: ')
        return redirect(url_for('index'))


@app.route('/raw', defaults={'req_path': ''})
@app.route('/raw/<path:req_path>')
@login_required
def raw(req_path):
    base_dir = Config.get()['save_dir']

    # Joining the base and the requested path
    rel_path, tweet_id = req_path.split(':')
    abs_path = os.path.expanduser(os.path.join(base_dir, rel_path))

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    found_tweet = None
    for line in readlines(abs_path):
        tweet = json.loads(line)
        if tweet.get('id_str') == tweet_id:
            found_tweet = tweet
            break

    if not found_tweet:
        return abort(404)

    tweet_json = json.dumps(found_tweet, indent=4)

    return render_template('raw_tweet.html', title=req_path, raw_tweet=tweet_json)


@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
@login_required
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
            title=f'{os.path.dirname(req_path)} ({len(tweets)})',
            nav=req_path,
            endpoint=os.path.dirname(req_path),
            items=tweets,
            filename=req_path
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
    return render_template(
        'files.html',
        title=f'{req_path or "root"} ({len(files)})',
        nav=req_path,
        items=files,
        path=req_path,
        status=crawler_status()
    )
