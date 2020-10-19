#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import faulthandler
import glob
import json
import os

import click

from collections import Counter
from datetime import datetime
from enum import Enum
from statistics import mean

from sqlalchemy import create_engine, exists, MetaData, Table
from sqlalchemy.orm import sessionmaker

from tqdm import tqdm

from twicorder.constants import (
    COMPRESSED_EXTENSIONS,
    REGULAR_EXTENSIONS,
)
from twicorder.exporter.tables import create_tables
from twicorder.exporter.tables import (
    Base,
    Hashtag,
    Media,
    Mention,
    Symbol,
    Tweet,
    Url,
    User,
)
from twicorder.utils import readlines, str_to_date


class Exporter:

    class Type(Enum):
        Tweet = 'tweet'
        User = 'user'

    def __init__(self, raw_data_path: str, output_path: str,
                 export_type: Type = Type.Tweet,
                 autostart: bool = False, new_only: bool = False):
        self._export_type = export_type
        self._new_only = new_only
        self._db_date = 0.0
        if os.path.isfile(output_path):
            self._db_date = os.path.getmtime(output_path)
        sqlite_path = f'sqlite:///{output_path}'
        engine = create_engine(sqlite_path)
        create_tables(engine)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()
        self.stats = {
            'skipped_tweets': 0,
            'exported_tweets': 0,
            'exported_users': 0,
            'skipped_users': 0
        }
        self._tweet_id_buffer = set()
        self._raw_data_path = raw_data_path

        if autostart:
            self.start()

    @property
    def root_path(self):
        return self._raw_data_path

    @property
    def tweet_id_buffer(self):
        """
        Buffer of tweet IDs for tweets that have been read, but which have not
        yet been committed to SQL.

        Returns:
            set[int]: Tweet IDs

        """
        return self._tweet_id_buffer

    def _collect_file_paths(self):
        """
        Collecting a list of all files to be ingested into database.

        Returns:
            list[str]: List of file paths

        """
        extensions = REGULAR_EXTENSIONS + COMPRESSED_EXTENSIONS
        search_pattern = os.path.join(self.root_path, '**', '*.*')
        paths = glob.glob(search_pattern, recursive=True)
        paths = [
            p for p in paths if os.path.splitext(p)[-1].strip('.') in extensions
        ]
        if self._new_only:
            hour = 3600
            grace_period = 6 * hour
            paths = [
                p for p in paths
                if os.path.getmtime(p) > self._db_date - grace_period
            ]
        return sorted(paths)

    @staticmethod
    def _get_tweet_type(tweet_obj):
        reply_status = tweet_obj.get('in_reply_to_status_id')
        reply_user = tweet_obj.get('in_reply_to_user_id')
        retweet = tweet_obj.get('retweeted_status')
        quote = tweet_obj.get('quoted_status')

        tweet_type = 'tw'
        if reply_status or reply_user:
            tweet_type = 're'
        if retweet:
            tweet_type = 'rt'
        elif quote:
            tweet_type = 'qt'
        return tweet_type

    @staticmethod
    def _get_endpoint(raw_file):
        tokens = [t for t in raw_file.split(os.sep) if t]
        if len(tokens) == 2 and tokens[0] == 'stream':
            return 'st'
        elif len(tokens) == 4:
            if tokens[2] == 'timeline':
                return 'tl'
            elif tokens[2] == 'mentions':
                return 'mt'
            elif tokens[2] == 'replies':
                return 'rp'
            elif tokens[1] == 'hashtags':
                return 'ht'

    @staticmethod
    def _get_tweet_text(tweet_obj):
        text_obj = tweet_obj.copy()
        if tweet_obj.get('retweeted_status'):
            text_obj = tweet_obj['retweeted_status'].copy()
        if text_obj.get('extended_tweet'):
            text_obj = text_obj['extended_tweet']
        text = text_obj.get('full_text', text_obj.get('text'))
        display_range = text_obj.get('display_text_range', (None, None))
        return text, display_range

    @staticmethod
    def _get_coordinates(coordinates_obj):
        if not coordinates_obj:
            return [None, None]
        return coordinates_obj['coordinates']

    @staticmethod
    def _get_coordinates_from_place(place_obj):
        if not place_obj:
            return [None, None]
        bounding_box = place_obj['bounding_box']
        if not bounding_box:
            return [None, None]
        coordinates = bounding_box['coordinates'][0]
        latitude = mean([c[0] for c in coordinates])
        longitude = mean([c[1] for c in coordinates])
        return [latitude, longitude]

    @classmethod
    def _recursive_update(cls, orig, new):
        shallow_new = {
            k: v for k, v in new.items() if v and not isinstance(v, dict)
        }
        orig.update(shallow_new)

        for key, value in new.items():
            if not isinstance(value, dict):
                continue
            cls._recursive_update(orig[key], value)

    @staticmethod
    def _extend_entities(tweet_obj):
        extended_entities = tweet_obj.get('extended_entities')
        if not extended_entities:
            return
        tweet_obj['entities']['media'] = extended_entities['media']

    def register_tweet(self, tweet_obj, raw_file, line, primary=True):
        tweet_id = tweet_obj['id']

        # Skip duplicates
        (ret,), = self.session.query(exists().where(Tweet.tweet_id == tweet_id))
        if ret or tweet_id in self.tweet_id_buffer:
            self.stats['skipped_tweets'] += 1
            return

        hashtags = []
        urls = []
        media_objects = []
        mentions = []

        # Copy retweet entities from original tweet
        if tweet_obj.get('retweeted_status'):
            retweeted_status = tweet_obj['retweeted_status']
            tweet_obj['entities'] = retweeted_status['entities']
            if retweeted_status.get('extended_entities'):
                extended_entities = retweeted_status['extended_entities']
                tweet_obj['extended_entities'] = extended_entities

        # Extend tweet
        if tweet_obj.get('extended_tweet'):
            extended_tweet = tweet_obj['extended_tweet']
            extended_entities = extended_tweet.pop('extended_entities', {})
            if extended_entities:
                tweet_obj['extended_entities'] = extended_entities
            self._recursive_update(tweet_obj, tweet_obj['extended_tweet'])

        # Extend entities
        self._extend_entities(tweet_obj)

        # Created date
        created_date = str_to_date(tweet_obj['created_at'])

        # Get end point
        endpoint = self._get_endpoint(raw_file)

        # Get tweet text
        text, text_range = self._get_tweet_text(tweet_obj)

        # Get location information
        place_obj = tweet_obj['place'] or {}
        place_id = place_obj.get('id')
        place_type = place_obj.get('place_type')
        place_full_name = place_obj.get('full_name')
        country_code = place_obj.get('country_code')
        latitude, longitude = self._get_coordinates(tweet_obj['coordinates'])
        if latitude and longitude:
            coordinates = True
        else:
            latitude, longitude = self._get_coordinates_from_place(place_obj)
            coordinates = False

        # Get withheld status
        withheld_in_countries_str = ','.join(
            tweet_obj.get('withheld_in_countries', [])
        )

        # Create raw file string
        raw_file_str = f'{raw_file}:{line}'

        # Register author
        capture_date = created_date if primary else None
        author = self.register_user(
            user_obj=tweet_obj['user'],
            tweet_id=tweet_id,
            endpoint=endpoint,
            capture_date=capture_date
        )

        # Register retweet
        retweet = tweet_obj.get('retweeted_status')
        if retweet:
            self.register_tweet(retweet, raw_file, line, primary=False)

        # Register quoted tweet
        quoted_status = tweet_obj.get('quoted_status')
        if quoted_status:
            self.register_tweet(quoted_status, raw_file, line, primary=False)

        # Register entities
        # Todo: Account for extended tweets from the streaming API
        for hashtag in tweet_obj['entities'].get('hashtags', []):
            self.register_hashtag(hashtag, tweet_id)
            hashtags.append(hashtag['text'])
        for symbol in tweet_obj['entities'].get('symbols', []):
            self.register_symbol(symbol, tweet_id)
        for url in tweet_obj['entities'].get('urls', []):
            self.register_url(url, tweet_id)
            urls.append(url)
        # Todo: Account for extended entities
        for media in tweet_obj['entities'].get('media', []):
            self.register_media(media, tweet_id)
            media_objects.append(media)
        for mention in tweet_obj['entities'].get('user_mentions', []):
            self.register_mention(
                mention_obj=mention,
                tweet_id=tweet_id,
                author=author,
                endpoint=endpoint,
                capture_date=capture_date
            )
            mentions.append(mention)

        # Register tweet
        tweet = Tweet(
            tweet_id=tweet_id,
            primary_capture=primary,
            endpoint=endpoint,
            created_at=str_to_date(tweet_obj['created_at']),
            tweet_type=self._get_tweet_type(tweet_obj),
            text=text,
            user_unique_id=author.unique_id,
            user_id=author.user_id,
            user_screen_name=author.screen_name,
            in_reply_to_status_id=tweet_obj['in_reply_to_status_id'],
            in_reply_to_user_id=tweet_obj['in_reply_to_user_id'],
            in_reply_to_screen_name=tweet_obj['in_reply_to_screen_name'],
            hashtags_str=','.join(sorted(hashtags)),
            hashtag_count=len(hashtags),
            url_count=len(urls),
            media_count=len(media_objects),
            retweet_status_id=retweet['id'] if retweet else None,
            is_quote_status=tweet_obj['is_quote_status'],
            quoted_status_id=quoted_status['id'] if quoted_status else None,
            mention_count=len(mentions),
            retweet_count=tweet_obj['retweet_count'],
            favorite_count=tweet_obj['favorite_count'],
            lang=tweet_obj['lang'],
            possibly_sensitive=tweet_obj.get('possibly_sensitive', False),
            display_start=text_range[0],
            display_end=text_range[1],
            character_count=len(text),
            coordinates=coordinates,
            place_id=place_id,
            place_type=place_type,
            place_full_name=place_full_name,
            country_code=country_code,
            latitude=latitude,
            longitude=longitude,
            withheld_copyright=tweet_obj.get('withheld_copyright'),
            withheld_in_countries_str=withheld_in_countries_str,
            raw_file=raw_file_str,
        )
        self.session.add(tweet)
        self.tweet_id_buffer.add(tweet_id)
        self.stats['exported_tweets'] += 1
        return tweet

    def register_user(self, user_obj, tweet_id, endpoint, capture_date=None):
        if 'created_at' not in user_obj:
            self.stats['skipped_users'] += 1
            return
        user = User(
            user_id=user_obj['id'],
            name=user_obj['name'],
            screen_name=user_obj['screen_name'],
            endpoint=endpoint,
            capture_date=capture_date,
            location=user_obj['location'],
            description=user_obj['description'],
            url=user_obj['url'],
            protected=user_obj['protected'],
            followers_count=user_obj['followers_count'],
            friends_count=user_obj['friends_count'],
            listed_count=user_obj['listed_count'],
            favourites_count=user_obj['favourites_count'],
            created_at=str_to_date(user_obj['created_at']),
            verified=user_obj['verified'],
            statuses_count=user_obj['statuses_count'],
            lang=user_obj['lang'],
            geo_enabled=user_obj['geo_enabled'],
            contributors_enabled=user_obj['contributors_enabled'],
            withheld_in_countries=','.join(user_obj.get('withheld_in_countries', ())),
            tweet_id=tweet_id
        )
        self.session.add(user)
        self.stats['exported_users'] += 1
        return user

    def register_hashtag(self, hashtag_obj, tweet_id):
        text = hashtag_obj['text']
        start, end = hashtag_obj['indices']
        hashtag = Hashtag(
            text=text,
            display_start=start,
            display_end=end,
            tweet_id=tweet_id
        )
        self.session.add(hashtag)
        return hashtag

    def register_symbol(self, symbol_obj, tweet_id):
        start, end = symbol_obj['indices']
        symbol = Symbol(
            text=symbol_obj['text'],
            display_start=start,
            display_end=end,
            tweet_id=tweet_id
        )
        self.session.add(symbol)
        return symbol

    def register_mention(self, mention_obj, tweet_id, endpoint, author=None,
                         capture_date=None):
        if author.user_id == mention_obj['id']:
            user = author
        else:
            user = self.register_user(
                user_obj=mention_obj,
                tweet_id=tweet_id,
                endpoint=endpoint,
                capture_date=capture_date
            )
        start, end = mention_obj['indices']
        mention = Mention(
            display_start=start,
            display_end=end,
            unique_user_id=user.unique_id if user else None,
            user_id=mention_obj['id'],
            tweet_id=tweet_id,
            name=mention_obj['name'],
            screen_name=mention_obj['screen_name']
        )
        self.session.add(mention)
        return mention

    def register_media(self, media_obj, tweet_id):
        start, end = media_obj['indices']
        media = Media(
            media_id=media_obj['id'],
            media_url=media_obj['media_url'],
            url=media_obj['url'],
            expanded_url=media_obj['expanded_url'],
            media_type=media_obj['type'],
            display_start=start,
            display_end=end,
            source_status_id=media_obj.get('source_status_id'),
            tweet_id=tweet_id
        )
        self.session.add(media)
        return media

    def register_url(self, url_obj, tweet_id):
        start, end = url_obj['indices']
        url = Url(
            url=url_obj['url'],
            expanded_url=url_obj['expanded_url'],
            display_start=start,
            display_end=end,
            tweet_id=tweet_id
        )
        self.session.add(url)
        return url

    def _get_ingested_files(self):
        counter = Counter()
        raw_files = [r[0] for r in self.session.query(Tweet.raw_file).all()]
        for data in raw_files:
            file, line = data.split(':')
            counter[file] = max(counter[file], int(line))
        return dict(counter.most_common())

    def start(self):
        ingested_files = self._get_ingested_files()
        file_paths = self._collect_file_paths()
        t0 = datetime.now()
        click.echo('')
        progress_iter = tqdm(
            iterable=file_paths,
            desc='Exporting',
            unit='files', ncols=120
        )
        for file_path in progress_iter:
            self.tweet_id_buffer.clear()
            raw_file = file_path.replace(self.root_path, '')
            try:
                lines = readlines(file_path)
            except Exception:
                click.echo(' Failed to read '.center(80, '='))
                click.echo(raw_file)
                click.echo('=' * 80)
                raise
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            for idx, line in enumerate(lines):
                if idx + 1 < ingested_files.get(raw_file, 0):
                    click.echo(f'Already ingested: {raw_file}:{idx + 1}')
                    continue
                try:
                    data = json.loads(line)
                except Exception as error:
                    click.echo(error)
                    continue
                if not data.get('id'):
                    # Don't bother with delete messages
                    continue
                if self._export_type == Exporter.Type.Tweet:
                    tweet = self.register_tweet(data, raw_file, idx + 1)
                elif self._export_type == Exporter.Type.User:
                    user = self.register_user(
                        user_obj=data,
                        tweet_id=None,
                        endpoint='ul',
                        capture_date=mtime
                    )

            self.session.commit()

        formatter = {
            'type': f'{self._export_type.value}',
            'skipped': self.stats[f'skipped_{self._export_type.value}s'],
            'exported': self.stats[f'exported_{self._export_type.value}s'],
            'time': datetime.now() - t0
        }

        click.echo(
            '\n'
            'Total exported {type}s: {exported}\n'
            'Duplicate {type}s skipped: {skipped}\n'
            'Total export time: {time}'
            .format_map(formatter)
        )


def expand_path(path: str) -> str:
    """
    Expand user and environment variables for the given path.

    Args:
        path: Path to expand

    Returns:
        Expanded path

    """
    return os.path.expanduser(os.path.expandvars(path))


@click.group()
@click.option('--input-dir', required=True, help='Raw data directory.')
@click.option('--output-dir', required=True, help='Export directory')
@click.option(
    '--new-only',
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        'If a database file exists, only export raw files created after the '
        'database was last modified.'
    )
)
@click.pass_context
def cli(ctx: click.Context, input_dir: str, output_dir: str, new_only: bool):
    """
    Twicorder raw data to SQLite exporter
    """
    faulthandler.enable()
    ctx.obj = dict(input_dir=input_dir, output_dir=output_dir, new_only=new_only)


@cli.command()
@click.pass_context
def users(ctx: click.Context):
    """
    User exporter
    """
    input_dir = expand_path(ctx.obj['input_dir'])
    output_dir = expand_path(ctx.obj['output_dir'])
    if not os.path.isdir(input_dir):
        click.echo(f'Raw data path was not found: {input_dir!r}')
        return
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception:
            click.echo(f'Unable to find or create output dir: {output_dir!r}')
            return
    output_path = os.path.join(output_dir, 'users.db')
    Exporter(
        input_dir,
        output_path,
        export_type=Exporter.Type.User,
        autostart=True,
        new_only=ctx.obj['new_only']
    )


@cli.command()
@click.pass_context
def tweets(ctx: click.Context):
    """
    Tweet exporter
    """
    input_dir = expand_path(ctx.obj['input_dir'])
    output_dir = expand_path(ctx.obj['output_dir'])
    if not os.path.isdir(input_dir):
        click.echo(f'Raw data path was not found: {input_dir!r}')
        return
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception:
            click.echo(f'Unable to find or create output dir: {output_dir!r}')
            return
    output_path = os.path.join(output_dir, 'tweets.db')
    Exporter(
        input_dir,
        output_path,
        export_type=Exporter.Type.Tweet,
        autostart=True,
        new_only=ctx.obj['new_only']
    )


if __name__ == '__main__':
    cli(auto_envvar_prefix='TC_EXPORT')
