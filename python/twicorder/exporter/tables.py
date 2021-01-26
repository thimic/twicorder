#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

"""
BigInteger: 64bit
Integer: 32bit
SmallInteger: 16bit
"""


class Tweet(Base):

    __tablename__ = 'tweets'

    # Primary Key
    tweet_id = Column(BigInteger, primary_key=True, index=True)

    primary_capture = Column(Boolean)
    endpoint = Column(String(2), index=True)
    created_at = Column(DateTime, index=True)
    tweet_type = Column(String(2), default='tw', index=True)
    text = Column(String(2048))

    # Foreign Keys
    user_unique_id = Column(BigInteger, ForeignKey('users.unique_id'), index=True)
    user_id = Column(BigInteger, index=True)
    user_screen_name = Column(String(64), index=True)

    # Attributes
    in_reply_to_status_id = Column(BigInteger)
    in_reply_to_user_id = Column(BigInteger)
    in_reply_to_screen_name = Column(String(64))

    hashtags_str = Column(String(2048))
    hashtag_count = Column(Integer, default=0)

    url_count = Column(Integer, default=0)
    media_count = Column(Integer, default=0)

    retweet_status_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    is_quote_status = Column(Boolean)
    quoted_status_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

    mention_count = Column(SmallInteger)
    retweet_count = Column(Integer)
    favorite_count = Column(Integer)

    lang = Column(String(8))
    possibly_sensitive = Column(Boolean, default=False)

    display_start = Column(SmallInteger)
    display_end = Column(SmallInteger)
    character_count = Column(SmallInteger)

    coordinates = Column(Boolean)
    place_id = Column(String(256))
    place_type = Column(String(64))
    place_full_name = Column(String(256))
    country_code = Column(String(2))
    latitude = Column(Float)
    longitude = Column(Float)

    withheld_copyright = Column(Boolean)
    withheld_in_countries_str = Column(String(256))

    raw_file = Column(String(256))

    # Relationships
    # user = relationship('User', uselist=False, back_populates='tweets')
    # retweet_status = relationship('Tweet', back_populates='tweets', foreign_keys=['retweet_status_id'])
    # quoted_status = relationship('Tweet', back_populates='tweets', foreign_keys=['quoted_status_id'])


class User(Base):

    __tablename__ = 'users'

    # Primary key
    unique_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(BigInteger, index=True)
    name = Column(String(64), index=True)
    screen_name = Column(String(64), index=True)
    endpoint = Column(String(2))
    capture_date = Column(DateTime)
    location = Column(String(256))
    description = Column(String(512))
    url = Column(String(256))
    protected = Column(Boolean)
    followers_count = Column(Integer)
    friends_count = Column(Integer)
    listed_count = Column(Integer)
    favourites_count = Column(Integer)

    created_at = Column(DateTime, index=True)
    verified = Column(Boolean)
    statuses_count = Column(Integer)
    lang = Column(String(8))
    geo_enabled = Column(Boolean)
    contributors_enabled = Column(Boolean)
    withheld_in_countries = Column(String(256))
    # tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    tweet_id = Column(BigInteger)

    # Releationships
    # tweet = relationship('Tweet', back_populates='users')


class Mention(Base):

    __tablename__ = 'mentions'

    # Primary key
    mention_id = Column(Integer, primary_key=True)

    # unique_user_id = Column(
    #     BigInteger, ForeignKey('users.unique_id'), index=True
    # )
    # tweet_id = Column(
    #     BigInteger, ForeignKey('tweets.tweet_id'), index=True
    # )
    unique_user_id = Column(BigInteger, index=True)
    tweet_id = Column(BigInteger, index=True)

    user_id = Column(BigInteger, index=True)
    display_start = Column(SmallInteger)
    display_end = Column(SmallInteger)
    name = Column(String(64), index=True)
    screen_name = Column(String(64), index=True)

    # Releationships
    # tweet = relationship('Tweet', back_populates='mentions')
    # user = relationship('User', back_populates='mentions')


class Hashtag(Base):

    __tablename__ = 'hashtags'

    # Primary key
    hashtag_id = Column(Integer, primary_key=True)

    text = Column(String(2048), index=True)
    display_start = Column(SmallInteger)
    display_end = Column(SmallInteger)
    # tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    tweet_id = Column(BigInteger)

    # Releationships
    # tweet = relationship('Tweet', back_populates='hashtags')


class Symbol(Base):

    __tablename__ = 'symbols'

    # Primary key
    symbol_id = Column(Integer, primary_key=True)

    text = Column(String(2048), index=True)
    display_start = Column(SmallInteger)
    display_end = Column(SmallInteger)
    # tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    tweet_id = Column(BigInteger)

    # Releationships
    # tweet = relationship('Tweet', back_populates='symbols')


class Media(Base):

    __tablename__ = 'media'

    # Primary key
    unique_id = Column(Integer, primary_key=True)

    media_id = Column(BigInteger, index=True)
    media_url = Column(String(2048))
    url = Column(String(512), index=True)
    expanded_url = Column(String(2048))
    media_type = Column(String(16), index=True)
    display_start = Column(SmallInteger)
    display_end = Column(SmallInteger)
    source_status_id = Column(BigInteger)
    # tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    tweet_id = Column(BigInteger)

    # Releationships
    # tweet = relationship('Tweet', back_populates='media')


class Url(Base):

    __tablename__ = 'urls'

    # Primary key
    url_id = Column(Integer, primary_key=True)

    url = Column(String(512), index=True)
    expanded_url = Column(String(2048))
    display_start = Column(SmallInteger)
    display_end = Column(SmallInteger)
    # tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    tweet_id = Column(BigInteger)

    # Releationships
    # tweet = relationship('Tweet', back_populates='urls')


def create_tables(engine):
    """
    Create all tables in the engine. This is equivalent to "Create Table"
    statements in raw SQL.

    Args:
        engine (Engine): SQLAlchemy engine

    """
    Base.metadata.create_all(engine)
