#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.getenv('TC_WEB_CONFIG') or basedir
db_name = 'twicorder-web.db'


class WebConfig(object):
    SECRET_KEY = os.getenv('TC_WEB_SECRET_KEY', os.urandom(36))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(db_dir, db_name)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
