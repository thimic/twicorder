#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from tweepy import OAuthHandler
from tweepy.auth import AppAuthHandler
from twicorder.utils import Singleton


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


def get_token_auth():
    """
    Loads login credentials from environment variables and instantiates a
    bearer token.

    Returns:
        OAuth2Bearer: Bearer token

    """
    auth = AppAuthHandler(
        consumer_key=os.getenv('CONSUMER_KEY'),
        consumer_secret=os.getenv('CONSUMER_SECRET')
    )
    bearer = auth.apply_auth()
    return bearer


class Auth(object, metaclass=Singleton):
    """
    Singleton for accessing the Auth handler
    """

    _handler = get_auth_handler()

    def __new__(cls, *args, **kwargs):
        return cls._handler


class TokenAuth(object, metaclass=Singleton):
    """
    Singleton for accessing the Bearer Token
    """

    _handler = get_token_auth()

    def __new__(cls, *args, **kwargs):
        return cls._handler


if __name__ == '__main__':
    handler = get_auth_handler()
    print(handler.oauth)
