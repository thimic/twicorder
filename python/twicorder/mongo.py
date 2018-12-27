#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import json
import os

from datetime import datetime

from pymongo import MongoClient, TEXT
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

from twicorder.config import Config
from twicorder import utils

logger = utils.FileLogger.get()


def is_connected(entity):
    """
    Checks if client is still connected to database.

    Args:
        entity (object): MongoClient, Database or Collection object

    Returns:
        bool: True if connected, else False

    """
    if isinstance(entity, MongoClient):
        client = entity
    elif isinstance(entity, Database):
        client = entity.client
    elif isinstance(entity, Collection):
        client = entity.database.client
    else:
        error = (
            'Please provide an instance of MongoClient, Database or Collection.'
        )
        raise TypeError(error)
    try:
        client.server_info()
    except ServerSelectionTimeoutError:
        return False
    return True


def create_collection(db_name='slpng_giants', collection_name='tweets'):
    """
    Create collection for the given database. Skip an return early if collection
    exists.

    Args:
        db_name (str): Database name
        collection_name (str): Collection name

    Returns:
        Collection: Created collection.

    """
    try:
        client = MongoClient()
        db = client[db_name]
        if collection_name in db.list_collection_names():
            return db[collection_name]
        collection = db[collection_name]
        collection.create_index('id', unique=True)
        collection.create_index('created_at')
        collection.create_index('retweet_count')
        collection.create_index('favorite_count')
        collection.create_index('in_reply_to_status_id')
        collection.create_index('in_reply_to_user_id')
        collection.create_index('in_reply_to_screen_name')
        collection.create_index('entities.hashtags')
        collection.create_index('user.created_at')
        collection.create_index('user.screen_name')
        collection.create_index('user.id')
        collection.create_index('user.followers_count')
        collection.create_index('user.favourites_count')
        collection.create_index('user.verified')
        collection.create_index('user.statuses_count')
        collection.create_index([('full_text', TEXT)])
        return collection
    except Exception:
        logger.exception('Unable to connect to MongoDB: ')
        return


def backfill(path=None, db_name='slpng_giants', collection_name='tweets'):
    logger = utils.FileLogger.get()
    tweets = create_collection(db_name, collection_name)

    config = Config.get()
    save_dir = os.path.expanduser(path or config['save_dir'])

    paths = glob.glob(os.path.join(save_dir, '**', '*.t*'), recursive=True)
    t0 = datetime.now()
    for idx, path in enumerate(paths):
        if os.path.basename(os.path.dirname(path)) != 'stream':
            continue
        try:
            for lidx, line in enumerate(utils.readlines(path)):
                try:
                    data = json.loads(line)
                except Exception:
                    logger.exception(
                        f'Backfill: Unable to read line {path}:{lidx + 1}'
                    )
                    continue
                else:
                    if data.get('delete'):
                        continue
                    if os.path.basename(os.path.dirname(path)) == 'stream':
                        data = utils.stream_to_search(data)
                    data = utils.timestamp_to_datetime(data)
                    tweets.replace_one({'id': data['id']}, data, upsert=True)
            t_delta = datetime.now() - t0
            average = t_delta / (idx + 1)
            remaining = str((len(paths) - (idx + 1)) * average).split('.')[0]

            logger.info(
                f'{idx + 1}/{len(paths)} '
                f'{remaining} '
                f'{os.sep.join(path.split(os.sep)[-3:])}'
            )
        except Exception:
            logger.exception(f'Backfill: Unable to read file: {path}')


if __name__ == '__main__':
    backfill()
