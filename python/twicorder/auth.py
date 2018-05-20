#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import yaml

from tweepy import OAuthHandler
from twicorder.constants import CONFIG_DIR


def get_auth_handler():
    """
    Loads login credentials from auth.yaml and instantiates an authentication
    handler.

    Returns:
        tweepy.OAuthHandler: Authentication handler

    """
    auth_path = os.path.join(CONFIG_DIR, 'auth.yaml')
    with open(auth_path, 'r') as stream:
        auth_dict = yaml.load(stream)
    auth_handler = OAuthHandler(**auth_dict['application'])
    auth_handler.set_access_token(**auth_dict['user'])
    return auth_handler
