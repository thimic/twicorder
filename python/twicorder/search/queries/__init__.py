#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import requests
import shelve
import time
import urllib

from datetime import datetime

from twicorder.auth import Auth, TokenAuth
from twicorder.config import Config
from twicorder.constants import APP_DATA_TOKEN
from twicorder.search.exchange import RateLimitCentral
from twicorder.utils import write


class QueryTracker(object):

    @staticmethod
    def get(uid):
        with shelve.open(APP_DATA_TOKEN) as db:
            value = db.get(uid)
        return value

    @staticmethod
    def put(uid, value):
        with shelve.open(APP_DATA_TOKEN) as db:
            db[uid] = value


class BaseQuery(object):

    _name = NotImplemented
    _endpoint = NotImplemented
    _since = NotImplemented
    _max_count = NotImplemented
    _results_path = NotImplemented
    _fetch_more_path = NotImplemented

    def __init__(self, output=None, **kwargs):
        self._done = False
        self._more_results = None
        self._results = []
        self._last_item = None
        self._output = output
        self._kwargs = kwargs
        self._orig_kwargs = kwargs.copy()

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
    def since(self):
        return self._since

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
    def last_item(self):
        return self._last_item

    @last_item.setter
    def last_item(self, value):
        self._last_item = value

    @property
    def results(self):
        return self._results

    def run(self):
        raise NotImplementedError

    def save(self):
        config = Config.get()
        save_root = config.get('save_dir')
        save_dir = os.path.join(save_root, self.name, self.output or self.uid)
        postfix = config.get('save_postfix')
        now = datetime.now()
        filename = f'{now:%Y-%m-%d_%H-%M-%S.%f}{postfix}'
        file_path = os.path.join(save_dir, filename)
        results_str = '\n'.join(json.dumps(r) for r in self.results)
        write(f'{results_str}\n', file_path)
        print(f'Wrote {len(self.results)} to "{file_path}"')
        if not self.last_item:
            self.last_item = self.results[0].get('id_str')
            QueryTracker.put(self.uid, self.last_item)


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
    _results_path = 'results'
    _fetch_more_path = 'next'

    _hash_keys = [
        '_endpoint',
        '_results_path',
        '_fetch_more_path',
        '_orig_kwargs',
        '_base_url',
    ]

    def __init__(self, output=None, **kwargs):
        super(RequestQuery, self).__init__(output, **kwargs)
        since = QueryTracker.get(self.uid)
        if since:
            self.kwargs[self.since] = since

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
        limit = RateLimitCentral().get(self.endpoint)
        print(limit)
        if limit and limit.remaining == 0:
            sleep_time = max(limit.reset - time.time(), 0) + 2
            msg = (
                f'Sleeping for {sleep_time:.02f} seconds for endpoint '
                f'"{self.endpoint}".'
            )
            print(msg)
            time.sleep(sleep_time)
        if self._token_auth:
            request = getattr(requests, self.request_type)
            response = request(
                self.request_url, data=json.dumps(self.kwargs), auth=TokenAuth()
            )
        else:
            request = getattr(Auth().oauth, self.request_type)
            response = request(self.request_url)
        if response.status_code != 200:
            if response.status_code == 429:
                print(f'Rate Limit in effect: {response.reason}')
                print(f'Message: {response.json().get("message")}')
            else:
                print('<{r.status_code}> {r.reason}: {r.content}'.format(r=response))
            return
        RateLimitCentral().update(self.endpoint, response.headers)
        pagination = response.json()
        for token in self.fetch_more_path.split('.'):
            pagination = pagination.get(token, {})
        if pagination:
            self._more_results = pagination
        else:
            self._more_results = None
            self._done = True
        results = response.json()
        for token in self.results_path.split('.'):
            results = results.get(token, [])
        self._results = results
        if results:
            self.save()
        return results
