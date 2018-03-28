#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml

from listener.constants import THIS_DIR

from tweepy import OAuthHandler


def get_auth_handler():
    """
    Loads login credentials from auth.yaml and instantiates an authentication
    handler.

    Returns:
        tweepy.OAuthHandler: Authentication handler

    """
    auth_path = os.path.join(THIS_DIR, 'config', 'auth.yaml')
    with open(auth_path, 'r') as stream:
        auth_dict = yaml.load(stream)
    auth_handler = OAuthHandler(auth_dict['consumer_key'], auth_dict['consumer_secret'])
    auth_handler.set_access_token(auth_dict['access_token'], auth_dict['access_secret'])
    return auth_handler
