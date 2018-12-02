#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
basedir = os.path.abspath(os.path.dirname(__file__))


class WebConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(36))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'twicorder.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
