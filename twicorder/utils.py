#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
