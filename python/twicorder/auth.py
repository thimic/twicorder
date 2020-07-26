#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tweepy import OAuthHandler
from tweepy.auth import AppAuthHandler, OAuth2Bearer
from twicorder.utils import Singleton


def get_auth_handler(consumer_key: str, consumer_secret: str,
                     access_token: str, access_secret: str) -> OAuthHandler:
    """
    Loads login credentials from environment variables and instantiates an
    authentication handler.

    Returns:
        Authentication handler

    """
    auth_handler = OAuthHandler(consumer_key, consumer_secret)
    auth_handler.set_access_token(access_token, access_secret)
    return auth_handler


def get_token_auth(consumer_key: str, consumer_secret: str) -> OAuth2Bearer:
    """
    Loads login credentials from environment variables and instantiates a
    bearer token.

    Args:
        consumer_key: Consumer Key
        consumer_secret: Consumer Secret

    Returns:
        OAuth2Bearer: Bearer token

    """
    auth = AppAuthHandler(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret
    )
    bearer = auth.apply_auth()
    return bearer


class Auth(object, metaclass=Singleton):
    """
    Singleton for accessing the Auth handler
    """

    _handler = None

    def __new__(cls, *args, **kwargs):
        cls._handler = get_auth_handler()
        return cls._handler


class TokenAuth(object, metaclass=Singleton):
    """
    Singleton for accessing the Bearer Token
    """

    _handler = None

    def __new__(cls, *args, **kwargs):
        cls._handler = get_token_auth()
        return cls._handler
