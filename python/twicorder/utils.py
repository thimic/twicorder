#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sqlite3
import sys

from datetime import datetime
from gzip import GzipFile
from logging import FileHandler, StreamHandler

from twicorder.constants import (
    REGULAR_EXTENSIONS, COMPRESSED_EXTENSIONS, USER_DIR, TW_TIME_FORMAT
)


class FileLogger(object):

    @staticmethod
    def get():
        log_path = os.path.join(USER_DIR, 'logs', 'twicorder.log')
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        logger = logging.getLogger('TwiCorder')
        file_handler = FileHandler(log_path)
        formatter = logging.Formatter(
            '%(asctime)s: [%(levelname)s] %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.WARNING)
        logger.addHandler(file_handler)

        stream_handler = StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        logger.addHandler(stream_handler)

        logger.setLevel(logging.DEBUG)

        return logger


class Singleton(type):
    """
    Class that can only be instanciated once.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def auto_commit(func):
    def func_wrapper(self, *args, **kwargs):
        with self._conn:
            func(self, *args, **kwargs)
    return func_wrapper


class AppData(object):
    """
    Class for reading and writing AppData to be used between sessions.
    """

    _data_path = os.path.join(USER_DIR, 'AppData')

    def __init__(self):
        if not os.path.exists(self._data_path):
            os.makedirs(self._data_path)
        filepath = os.path.join(self._data_path, 'twicorder.sql')
        self._conn = sqlite3.connect(
            filepath,
            isolation_level=None,
            check_same_thread=True
        )

    def __del__(self):
        self._conn.close()

    def _make_query_table(self, name):
        cursor = self._conn.cursor()
        cursor.execute(
            f'''
            CREATE TABLE IF NOT EXISTS [{name}] (
                tweet_id INTEGER PRIMARY KEY,
                timestamp INTEGER NOT NULL
            )
            '''
        )

    def _make_last_id_table(self):
        cursor = self._conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS queries_last_id (
                query_hash TEXT PRIMARY KEY,
                tweet_id INTEGER NOT NULL
            )
            '''
        )

    def add_query_tweet(self, query_name, tweet_id, timestamp):
        self._make_query_table(query_name)
        cursor = self._conn.cursor()
        cursor.execute(
            f'''
            INSERT OR REPLACE INTO {query_name} VALUES (
                ?, ?
            )
            ''',
            (tweet_id, timestamp)
        )

    def add_query_tweets(self, query_name, tweets):
        self._make_query_table(query_name)
        cursor = self._conn.cursor()
        cursor.executemany(
            f'''
            INSERT OR REPLACE INTO {query_name} VALUES (
                ?, ?
            )
            ''',
            tweets
        )

    def get_query_tweets(self, query_name):
        self._make_query_table(query_name)
        cursor = self._conn.cursor()
        cursor.execute(
            f'''
            SELECT DISTINCT
                tweet_id, timestamp
            FROM
                {query_name}
            '''
        )
        return cursor.fetchall()

    def set_last_query_id(self, query_hash, tweet_id):
        self._make_last_id_table()
        cursor = self._conn.cursor()
        cursor.execute(
            '''
            INSERT OR REPLACE INTO queries_last_id VALUES (
                ?, ?
            )
            ''',
            (query_hash, tweet_id)
        )

    def get_last_query_id(self, query_hash):
        self._make_last_id_table()
        cursor = self._conn.cursor()
        cursor.execute(
            '''
            SELECT
            DISTINCT
                tweet_id
            FROM
                queries_last_id
            WHERE
                query_hash=?
            ''',
            (query_hash,)
        )
        result = cursor.fetchone()
        if not result:
            return
        return result[0]


def twopen(filename, mode='r'):
    """
    Replacement method for Python's build-in open. Adds the option to handle
    compressed files.

    Args:
        filename (str): Path to file
        mode (str): Open mode

    Returns:
        TextIOWrapper / GzipFile: File object

    Raises:
        IOError: If extension is unknown.

    """
    filename = os.path.expanduser(filename)
    dirname = os.path.dirname(filename)
    if mode in ('a', 'w') and not os.path.isdir(dirname):
        os.makedirs(dirname)
    ext = os.path.splitext(filename)[-1].strip('.')
    if ext in REGULAR_EXTENSIONS:
        return open(file=filename, mode=mode)
    elif ext in COMPRESSED_EXTENSIONS:
        return GzipFile(filename=filename, mode=mode)
    else:
        raise IOError('Unrecognised format: {}'.format(ext))


def read(filename):
    """
    Reading the file for a given path.

    Args:
        filename (str): Path to file to read

    Returns:
        str: File data

    """
    with twopen(filename=filename, mode='r') as file_object:
        data = file_object.read()
        if isinstance(file_object, GzipFile):
            data = data.decode('utf-8')
        return data


def readlines(filename):
    """
    Reading the file for a given path.

    Args:
        filename (str): Path to file to read

    Returns:
        str: File data

    """
    with twopen(filename=filename, mode='r') as file_object:
        data = file_object.readlines()
        if isinstance(file_object, GzipFile):
            data = [d.decode('utf-8') for d in data]
        return data


def write(data, filename, mode='a'):
    """
    Appending data to the given file.

    Args:
        data (str): Data to append to the given file
        filename (str): Path to file to write
        mode (str): File stream mode ('a'. 'w' etc)

    """
    with twopen(filename=filename, mode=mode) as file_object:
        if isinstance(file_object, GzipFile):
            file_object.write(data.encode('utf-8'))
            return
        file_object.write(data)


def message(title='Warning', body='', width=80):
    """
    Prints a formatted message based on input

    Args:
        title (str): Title of the message
        body (str): Message body
        width (int): Message line width

    """
    header = ' {} '.format(title).center(width, '=')
    footer = '=' * width
    text = (
        '\n'
        '{}\n'
        '\n'
        '{}\n'
        '\n'
        '{}\n'
        '\n'
    )
    print(text.format(header, body, footer))


def collect_key_values(key, data):
    """
    Builds a list of values for all keys matching the given "key" in a nested
    dictionary.

    Args:
        key (object): Dictionary key to search for
        data (dict): Nested data dict

    Returns:
        list: List of values for given key

    """
    values = []
    for k, v in data.items():
        if k == key:
            values.append(v)
            continue
        if isinstance(v, dict):
            values += collect_key_values(key, v)
    return values


def flatten(l):
    """
    Flattens a nested list

    Args:
        l (list): Nested list

    Returns:
        list: Flattened list

    """
    return [item for sublist in l for item in sublist]


def timestamp_to_datetime(data):
    """
    Traverse dictionary and convert all instances of time stamp strings into
    datetime objects.

    Args:
        data (dict): Tweet dictionary

    Returns:
        dict: Updated tweet dictionary

    """
    for key, value in data.items():
        if key in ['created_at', 'recorded_at'] and isinstance(value, str):
            data[key] = datetime.strptime(value, TW_TIME_FORMAT)
        elif isinstance(value, dict):
            data[key] = timestamp_to_datetime(value)
        elif isinstance(value, list):
            data[key] = [timestamp_to_datetime(v) for v in value if isinstance(v, dict)]
    return data


def stream_to_search(data):
    """
    Conform tweet dictionaries collected from the streaming API to the format of
    tweets collected from the search API.

    Args:
        data (dict): Tweet dictionary

    Returns:
        dict: Updated tweet dictionary

    """
    extended_tweet = data.get('extended_tweet')
    if extended_tweet:
        data.pop('extended_tweet')
        data.update(extended_tweet)
        data['truncated'] = False
        data.pop('text')
    else:
        if data.get('text'):
            data['full_text'] = data.pop('text')
    for key, value in data.items():
        if key in ['retweeted_status', 'quoted_status']:
            data[key] = stream_to_search(value)
    return data
