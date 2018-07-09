#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from gzip import GzipFile
from twicorder.constants import REGULAR_EXTENSIONS, COMPRESSED_EXTENSIONS


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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


def find_key(key, data):
    """
    Searches a nested dictionary for a key and returns a list of all values for
    said key.

    Args:
        key (str): Key to search for
        data (dict): Dictionary to examine

    Returns:
        list: List of values for given key

    """
    found = []
    for k, v in data.items():
        if k == key:
            found.append(v)
            continue
        if isinstance(v, dict):
            found += find_key(key, v)
    return found
