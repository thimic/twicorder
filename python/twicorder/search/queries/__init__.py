#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import hashlib
import json
import os
import requests
import time
import traceback
import urllib

from datetime import datetime

from twicorder import mongo
from twicorder.auth import Auth, TokenAuth
from twicorder.config import Config
from twicorder.constants import TW_TIME_FORMAT
from twicorder.search.exchange import RateLimitCentral
from twicorder.utils import write, AppData, timestamp_to_datetime


class BaseQuery(object):

    _name = NotImplemented
    _endpoint = NotImplemented
    _max_count = NotImplemented
    _last_return_token = None
    _results_path = None
    _fetch_more_path = None

    _mongo_collection = None

    def __init__(self, output=None, **kwargs):
        self._done = False
        self._more_results = None
        self._results = []
        self._last_id = None
        self._output = output
        self._kwargs = kwargs
        self._orig_kwargs = copy.deepcopy(kwargs)
        self._log = []

        last_return = AppData().get_last_query_id(self.uid)
        if last_return:
            self.kwargs[self.last_return_token] = last_return

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __repr__(self):
        return f'Query({repr(self.name)}, kwargs={str(self.kwargs)})'

    @property
    def name(self):
        return self._name

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def output(self):
        return self._output

    @property
    def last_return_token(self):
        return self._last_return_token

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def max_count(self):
        return self._max_count

    @property
    def results_path(self):
        return self._results_path

    @property
    def fetch_more_path(self):
        return self._fetch_more_path

    @property
    def uid(self):
        raise NotImplementedError

    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, value):
        self._done = value

    @property
    def more_results(self):
        return self._more_results

    @property
    def last_id(self):
        return self._last_id

    @last_id.setter
    def last_id(self, value):
        self._last_id = value

    @property
    def results(self):
        return self._results

    @property
    def mongo_collection(self):
        if not self._mongo_collection or not mongo.is_connected(self._mongo_collection):
            self._mongo_collection = mongo.create_collection()
        return self._mongo_collection

    def run(self):
        raise NotImplementedError

    def log(self, line):
        self._log.append(line)

    def fetch_log(self):
        log_data = '\n' + f' {self.endpoint} '.center(80, '=') + '\n'
        log_data += '\n'.join(self._log)
        log_data += '\n' + '=' * 80
        return log_data

    def save(self):
        if not self._results or not self._output:
            return
        config = Config.get()
        save_root = config.get('output_dir')
        save_dir = os.path.join(save_root, self._output or self.uid)
        postfix = config.get('save_postfix')
        marker = self._results[0]
        stamp = datetime.strptime(marker['created_at'], TW_TIME_FORMAT)
        uid = marker['id']
        filename = f'{stamp:%Y-%m-%d_%H-%M-%S}_{uid}{postfix}'
        file_path = os.path.join(save_dir, filename)
        results_str = '\n'.join(json.dumps(r) for r in self._results)
        write(f'{results_str}\n', file_path)
        self.log(f'Wrote {len(self.results)} tweets to "{file_path}"')

        # Write to Mongo
        if not self.mongo_collection:
            return
        try:
            for result in self._results:
                data = copy.deepcopy(result)
                data = timestamp_to_datetime(data)
                self.mongo_collection.replace_one(
                    {'id': data['id']},
                    data,
                    upsert=True
                )
        except Exception:
            self.log(f'Unable to connect to MongoDB: {traceback.format_exc()}')
        else:
            self.log(f'Wrote {len(self.results)} tweets to MongoDB')

    def pickle(self):
        """
        Saves a cache of tweet IDs from query result to disk. In storing the IDs
        between sessions, we make sure we don't save already found tweets.

        To prevent the disk cache growing too large, we purge IDs for tweets
        older than 14 days. Twitter's base search only goes back 7 days, so we
        shouldn't encounter tweets older than 14 days very often.
        """

        # Loading picked tweet IDs
        tweets = dict(AppData().get_query_tweets(self._name)) or {}

        # # Purging tweet IDs older than 14 days
        # now = datetime.now()
        # old_tweets = tweets.copy()
        # tweets = {}
        # for tweet_id, timestamp in old_tweets.items():
        #     dt = datetime.fromtimestamp(timestamp)
        #     if not now - dt > timedelta(days=14):
        #         tweets[tweet_id] = timestamp

        # Stores tweet IDs from result
        self._results = [t for t in self.results if t['id'] not in tweets]
        new_tweets = []
        for result in self.results:
            created_at = result['created_at']
            dt = datetime.strptime(created_at, TW_TIME_FORMAT)
            timestamp = int(dt.timestamp())
            new_tweets.append((result['id'], timestamp))
        AppData().add_query_tweets(self._name, new_tweets)


class TweepyQuery(BaseQuery):

    def __init__(self, api, kwargs):
        super(TweepyQuery, self).__init__()
        self._api = api
        self._kwargs = kwargs

    @property
    def api(self):
        return self._api


class RequestQuery(BaseQuery):

    _base_url = 'https://api.twitter.com/1.1'
    _request_type = 'get'
    _token_auth = False

    _hash_keys = [
        '_endpoint',
        '_results_path',
        '_fetch_more_path',
        '_orig_kwargs',
        '_base_url',
    ]

    def __init__(self, output=None, **kwargs):
        super(RequestQuery, self).__init__(output, **kwargs)

    def __eq__(self, other):
        return type(self) == type(other) and self.uid == other.uid

    @property
    def base_url(self):
        return self._base_url

    @property
    def request_type(self):
        return self._request_type

    @property
    def token_auth(self):
        return self._token_auth

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    @property
    def uid(self):
        hash_str = str([getattr(self, k) for k in self._hash_keys]).encode()
        return hashlib.blake2s(hash_str).hexdigest()

    def run(self):
        # Purging logs
        self._log = []

        # Check rate limit for query. Sleep if limits are in effect.
        limit = RateLimitCentral().get(self.endpoint)
        self.log(f'URL: {self.request_url}')
        self.log(f'{limit}')
        if limit and limit.remaining == 0:
            sleep_time = max(limit.reset - time.time(), 0) + 2
            msg = (
                f'Sleeping for {sleep_time:.02f} seconds for endpoint '
                f'"{self.endpoint}".'
            )
            self.log(msg)
            time.sleep(sleep_time)

        # Perform query
        attempts = 0
        while True:
            try:
                if self._token_auth:
                    request = getattr(requests, self.request_type)
                    response = request(
                        self.request_url,
                        data=json.dumps(self.kwargs),
                        auth=TokenAuth()
                    )
                else:
                    request = getattr(Auth().oauth, self.request_type)
                    response = request(self.request_url)
            except Exception:
                attempts += 1
                self.log(traceback.format_exc())
                time.sleep(2**attempts)
                if attempts >= 5:
                    break
            else:
                break

        # Check query response code. Return with error message if not a
        # successful 200 code.
        if response.status_code != 200:
            if response.status_code == 429:
                self.log(f'Rate Limit in effect: {response.reason}')
                self.log(f'Message: {response.json().get("message")}')
            else:
                self.log(
                    '<{r.status_code}> {r.reason}: {r.content}'
                    .format(r=response)
                )
            return
        self.log('Successful return!')

        # Update rate limit for query
        RateLimitCentral().update(self.endpoint, response.headers)

        # Search query response for additional paged results. Pronounce the
        # query done if no more pages are found.
        pagination = response.json()
        if self.fetch_more_path:
            for token in self.fetch_more_path.split('.'):
                pagination = pagination.get(token, {})
            if pagination:
                self._more_results = pagination
                self.log('More pages found!')
            else:
                self._more_results = None
                self._done = True
                self.log('No more pages!')
        else:
            self._done = True

        # Extract crawled tweets from query response.
        results = response.json()
        if self.results_path:
            for token in self.results_path.split('.'):
                results = results.get(token, [])
        self._results = results
        self.log(f'Result count: {len(results)}')

        # Saves and stores IDs for crawled tweets found in the query result.
        # Also records the last tweet ID found.
        if results:
            self.pickle()
            self.log(f'Cached Tweet IDs to disk!')
            self.save()
            if self.last_id is None:
                self.last_id = results[0].get('id_str')

        # Caches last tweet ID found to disk if the query, including all pages
        # completed successfully. This saves us from searching all the way back
        # to the beginning on next crawl. Instead we can stop when we encounter
        # this tweet.
        if self._done and self.last_id:
            self.log(f'Cached ID of last tweet returned by query to disk.')
            AppData().set_last_query_id(self.uid, self.last_id)

        # Returning crawled results
        return results
