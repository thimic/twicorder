#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class BaseQuery(object):

    _endpoint = NotImplemented
    _args = []
    _kwargs = {}
    _response = None
    _max_count = NotImplemented

    @property
    def endpoint(self):
        return self._endpoint

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def response(self):
        return self._response

    @property
    def max_count(self):
        return self._max_count

    def run(self):
        raise NotImplementedError


class TweepyQuery(BaseQuery):

    def __init__(self, api, *args, **kwargs):
        self._api = api
        self._args = args
        self._kwargs = kwargs

    @property
    def api(self):
        return self._api


class RequestQuery(BaseQuery):

    _base_url = 'https://api.twitter.com/1.1'

    def __init__(self, auth, *args, **kwargs):
        self._auth = auth.oauth
        self._args = args
        self._kwargs = kwargs

    @property
    def auth(self):
        return self._auth

    @property
    def base_url(self):
        return self._base_url

    @property
    def request_url(self):
        if not self.kwargs.get('count'):
            self.kwargs['count'] = self.max_count
        kwargs = '&'.join([f'{k}={v}' for k, v in self.kwargs.items()])
        url = f'{self.base_url}{self.endpoint}.json'
        if kwargs:
            url += f'?{kwargs}'
        return url

    def run(self):
        self._response = self.auth.get(self.request_url)
        return self._response
