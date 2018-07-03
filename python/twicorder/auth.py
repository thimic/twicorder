#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from tweepy import OAuthHandler


def get_auth_handler():
    """
        Loads login credentials from environment variables and instantiates an
        authentication handler.

        Returns:
            tweepy.OAuthHandler: Authentication handler

        """
    app_auth = {
        'consumer_key': os.getenv('CONSUMER_KEY'),
        'consumer_secret': os.getenv('CONSUMER_SECRET')
    }
    user_auth = {
        'key': os.getenv('ACCESS_TOKEN'),
        'secret': os.getenv('ACCESS_SECRET')
    }
    auth_handler = OAuthHandler(**app_auth)
    auth_handler.set_access_token(**user_auth)
    return auth_handler


if __name__ == '__main__':
    handler = get_auth_handler()
    print(handler.oauth)
