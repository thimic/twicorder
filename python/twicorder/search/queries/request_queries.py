#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib

from twicorder.search.queries import RequestQuery


class TimelineQuery(RequestQuery):

    _name = 'user_timeline'
    _endpoint = '/statuses/user_timeline'


class StandardSearchQuery(RequestQuery):

    _name = 'free_search'
    _endpoint = '/search/tweets'
    _since = 'since_id'
    _results_path = 'statuses'
    _fetch_more_path = 'search_metadata.next_results'

    def __init__(self, output=None, **kwargs):
        super(StandardSearchQuery, self).__init__(output, **kwargs)
        self._kwargs.update({'result_type': 'recent', 'count': 100, 'include_entities': 1})
        self._kwargs.update(kwargs)

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.more_results:
                url += self.more_results
            elif self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url


class FullArchiveGetQuery(RequestQuery):

    _name = 'fullarchive_get'
    _endpoint = '/tweets/search/fullarchive/production'
    _fetch_more_path = 'next'


class FullArchivePostQuery(RequestQuery):

    _name = 'fullarchive_post'
    _endpoint = '/tweets/search/fullarchive/production'
    _fetch_more_path = 'next'
    _request_type = 'post'
    _token_auth = True


class FriendsList(RequestQuery):

    _name = 'friends_list'
    _endpoint = '/friends/list'


class RateLimitStatusQuery(RequestQuery):

    _name = 'rate_limit_status'
    _endpoint = '/application/rate_limit_status'


if __name__ == '__main__':
    query = StandardSearchQuery(
        q='@slpng_giants',
        result_type='recent',
        count=100,
        include_entities=1
    )
    print(query.uid)
    query2 = StandardSearchQuery(
        q='@slpng_giants_no',
        result_type='recent',
        count=100,
        include_entities=1
    )
    print(query2.uid)
