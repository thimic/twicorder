#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import urllib

from datetime import datetime, timedelta
from threading import Lock

from twicorder.utils import collect_key_values, Singleton
from twicorder.search.queries import RequestQuery


class CachedUser(object):

    def __init__(self, user_data):

        self._data = user_data
        self._timestamp = datetime.now()

    def __eq__(self, other):
        return type(self) == type(other) and self.uid == other.uid

    def __repr__(self):
        rep = (
            f'CachedUser('
            f'name={self.screen_name}, '
            f'timestamp={self.timestamp:%c}'
            f')'
        )
        return rep

    @property
    def uid(self):
        return self._data['id']

    @property
    def screen_name(self):
        return self._data['screen_name']

    @property
    def data(self):
        return self._data

    @property
    def timestamp(self):
        return self._timestamp


class CachedUserCentral(object, metaclass=Singleton):

    def __init__(self):
        self._users = {}
        self._cache_life = timedelta(minutes=15)
        self.lock = Lock()

    def add(self, user):
        self._users[user['id']] = CachedUser(user)

    def filter(self):
        self._users = {
            k: v for k, v in self._users.items()
            if datetime.now() - v.timestamp <= self._cache_life
        }

    @property
    def users(self):
        return self._users

    def expand_user_mentions(self, tweets):
        """
        Expands user mentions for tweets in result. Performs API user lookup if
        no data is found for the given mention.

        Args:
            tweets (list[dict]): List of tweets

        Returns:
            list[dict]: List of tweets with expanded user mentions

        """
        with self.lock:
            self.filter()
            missing_users = set([])
            for tweet in tweets:
                for user in collect_key_values('user', tweet):
                    self.add(user)
                mention_sections = collect_key_values('user_mentions', tweet)
                for mention_section in mention_sections:
                    for mention in mention_section:
                        if not mention['id'] in self.users:
                            missing_users.add(mention['id'])
            if not missing_users:
                return
            missing_users = list(missing_users)
            n = 100
            chunks = [
                missing_users[i:i + n] for i in range(0, len(missing_users), n)
            ]
            for chunk in chunks:
                UserQuery(user_id=','.join([str(u) for u in chunk])).run()
            for tweet in tweets:
                mention_sections = collect_key_values('user_mentions', tweet)
                for mention_section in mention_sections:
                    for mention in mention_section:
                        full_user = self.users.get(mention['id'])
                        if not full_user:
                            continue
                        mention.update(full_user.data)
        return tweets


class UserQuery(RequestQuery):

    _name = 'user'
    _endpoint = '/users/lookup'

    def __init__(self, output=None, **kwargs):
        super(UserQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    def pickle(self):
        return

    def save(self):
        for user in self.results:
            CachedUserCentral().add(user)


class StatusQuery(RequestQuery):

    _name = 'status'
    _endpoint = '/statuses/lookup'

    def __init__(self, output=None, **kwargs):
        super(StatusQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['include_entities'] = 'true'
        self._kwargs['trim_user'] = 'false'
        self._kwargs.update(kwargs)

    def save(self):
        for status in self.results:
            pass


class TimelineQuery(RequestQuery):

    _name = 'user_timeline'
    _endpoint = '/statuses/user_timeline'
    _last_return_token = 'since_id'

    def __init__(self, output=None, **kwargs):
        super(TimelineQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['result_type'] = 'recent'
        self._kwargs['count'] = 200
        self._kwargs['trim_user'] = 'false'
        self._kwargs['exclude_replies'] = 'false'
        self._kwargs['include_rts'] = 'true'
        self._kwargs.update(kwargs)

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.more_results:
                self.kwargs['max_id'] = self.more_results
            url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    def run(self):
        super(TimelineQuery, self).run()
        self.done = False
        if not self.results:
            self.done = True
            return
        self._more_results = self.results[-1]['id_str']
        last_return = self.kwargs.get('max_id')
        if last_return and int(self._more_results) >= int(last_return):
            self.done = True

    def save(self):
        self.log('Expanding user mentions!')
        CachedUserCentral().expand_user_mentions(self.results)
        super(TimelineQuery, self).save()


class StandardSearchQuery(RequestQuery):

    _name = 'free_search'
    _endpoint = '/search/tweets'
    _last_return_token = 'since_id'
    _results_path = 'statuses'
    _fetch_more_path = 'search_metadata.next_results'

    def __init__(self, output=None, **kwargs):
        super(StandardSearchQuery, self).__init__(output, **kwargs)
        self._kwargs['tweet_mode'] = 'extended'
        self._kwargs['result_type'] = 'recent'
        self._kwargs['count'] = 100
        self._kwargs['include_entities'] = 'true'
        self._kwargs.update(kwargs)

    @property
    def request_url(self):
        url = f'{self.base_url}{self.endpoint}.json'
        if self.request_type == 'get':
            if self.more_results:
                url += self.more_results
                # API bug: 'search_metadata.next_results' does not include
                # 'tweet_mode'. Adding it back in manually.
                if 'tweet_mode=extended' not in url:
                    url += '&tweet_mode=extended'
            elif self.kwargs:
                url += f'?{urllib.parse.urlencode(self.kwargs)}'
        return url

    def save(self):
        self.log('Expanding user mentions!')
        CachedUserCentral().expand_user_mentions(self.results)
        super(StandardSearchQuery, self).save()


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
