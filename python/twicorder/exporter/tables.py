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

    created_at = Column(DateTime, index=True)
    tweet_type = Column(String(2), default='tw', index=True)
    text = Column(String(1024), index=True)

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey('users.unique_id'), index=True)

    # Attributes
    in_reply_to_status_id = Column(BigInteger)
    in_reply_to_user_id = Column(BigInteger)
    in_reply_to_screen_name = Column(String(64))

    hashtags_str = Column(String(512))
    hashtag_count = Column(Integer, default=0, index=True)

    url_count = Column(Integer, default=0, index=True)

    retweet_status_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))
    is_quote_status = Column(Boolean, index=True)
    quoted_status_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

    mention_count = Column(SmallInteger, index=True)
    retweet_count = Column(Integer, index=True)
    favourite_count = Column(Integer, index=True)

    lang = Column(String(8), index=True)
    possibly_sensitive = Column(Boolean, index=True)

    display_start = Column(SmallInteger, index=True)
    display_end = Column(SmallInteger, index=True)
    character_count = Column(SmallInteger, index=True)

    coordinates = Column(Boolean, index=True)
    place_id = Column(String(256))
    place_type = Column(String(64))
    place_full_name = Column(String(256))
    country_code = Column(String(2), index=True)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)

    withheld_copyright = Column(Boolean, index=True)
    withheld_in_countries_str = Column(String(256))

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
    location = Column(String(256))
    description = Column(String(512))
    url = Column(String(256))
    protected = Column(Boolean, index=True)
    followers_count = Column(Integer, index=True)
    friends_count = Column(Integer, index=True)
    listed_count = Column(Integer, index=True)
    favourites_count = Column(Integer, index=True)

    created_at = Column(DateTime, index=True)
    verified = Column(Boolean, index=True)
    statuses_count = Column(Integer, index=True)
    lang = Column(String(8), index=True)
    geo_enabled = Column(Boolean, index=True)
    contributors_enabled = Column(Boolean, index=True)
    withheld_in_countries = Column(String(256))
    tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

    # Releationships
    # tweet = relationship('Tweet', back_populates='users')


class Mention(Base):

    __tablename__ = 'mentions'

    # Primary keys
    unique_user_id = Column(
        BigInteger, ForeignKey('users.unique_id'), primary_key=True, index=True
    )
    tweet_id = Column(
        BigInteger, ForeignKey('tweets.tweet_id'), primary_key=True, index=True
    )
    display_start = Column(SmallInteger, index=True)
    display_end = Column(SmallInteger, index=True)

    # Releationships
    # tweet = relationship('Tweet', back_populates='mentions')
    # user = relationship('User', back_populates='mentions')


class Hashtag(Base):

    __tablename__ = 'hashtags'

    # Primary key
    hashtag_id = Column(Integer, primary_key=True)

    text = Column(String(512), index=True)
    display_start = Column(SmallInteger, index=True)
    display_end = Column(SmallInteger, index=True)
    tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

    # Releationships
    # tweet = relationship('Tweet', back_populates='hashtags')


class Symbol(Base):
    __tablename__ = 'symbols'

    # Primary key
    symbol_id = Column(Integer, primary_key=True)

    text = Column(String(512), index=True)
    display_start = Column(SmallInteger, index=True)
    display_end = Column(SmallInteger, index=True)
    tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

    # Releationships
    # tweet = relationship('Tweet', back_populates='symbols')


class Media(Base):

    __tablename__ = 'media'

    # Primary key
    media_id = Column(BigInteger, primary_key=True)

    media_url = Column(String(2048))
    url = Column(String(512), index=True)
    expanded_url = Column(String(2048))
    media_type = Column(String(16), index=True)
    display_start = Column(SmallInteger, index=True)
    display_end = Column(SmallInteger, index=True)
    source_status_id = Column(BigInteger)
    tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

    # Releationships
    # tweet = relationship('Tweet', back_populates='media')


class Url(Base):

    __tablename__ = 'urls'

    # Primary key
    url_id = Column(Integer, primary_key=True)

    url = Column(String(512), index=True)
    expanded_url = Column(String(2048))
    display_start = Column(SmallInteger, index=True)
    display_end = Column(SmallInteger, index=True)
    tweet_id = Column(BigInteger, ForeignKey('tweets.tweet_id'))

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
