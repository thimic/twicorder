#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from twicorder.search.queries import RequestQuery


class TimelineQuery(RequestQuery):

    _endpoint = '/statuses/user_timeline'
    _max_count = 200


if __name__ == '__main__':
    import json
    import tweepy
    from twicorder.auth import get_auth_handler

    handler = get_auth_handler()
    api = tweepy.API(handler)

    query = TimelineQuery(auth=handler, screen_name='slpng_giants')
    response = query.run()
    print(response.content.decode())
    print(response.headers)
