#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymongo import MongoClient, TEXT


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
