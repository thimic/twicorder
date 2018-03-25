#!/usr/bin/env python3

import copy
import json


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


def update_key(key, value, data):
    """
    Searches a nested dictionary for a key and updates all corresponding values
    that are dictionaries or lists of dictionaries with the value dictionary.

    Args:
        key (str): Key to search for
        value (dict): A dictionary of values to update found dictionaries with
        data (dict): Dictionary to examine

    Returns:
        dict: Updated dictionary

    """
    _data = copy.deepcopy(data)
    for k in _data:
        v = _data[k]
        if k == key:
            if isinstance(v, dict):
                _data[k].update(value)
                continue
            elif isinstance(v, list):
                for i in _data[k]:
                    i.update(value)
                continue
        if not isinstance(v, dict):
            continue
        _data[k] = update_key(key, value, _data[k])
    return _data


def flatten(_list):
    """
    Flattens a nested list.

    Args:
        _list (list): List to be flattened

    Returns:
        list: Flattened list

    """
    master_list = []
    for item in _list:
        if isinstance(item, list):
            master_list += flatten(item)
            continue
        master_list.append(item)
    json_list = list(set([json.dumps(i) for i in master_list]))
    return [json.loads(l) for l in json_list]


if __name__ == '__main__':
    # test = {
    #     'user_mentions': [{'foo': 'bar'}, {'foo': 'gah'}, {'foo': 'meh'}],
    #     'test': 1,
    #     'la': {'user_mentions': [{'test': 'mess'}], 'fnugg': 'tra'},
    #     'gah': {'user_mentions': {'test': 'mess'}, 'fnugg': 'tra'},
    # }
    # import pprint
    # pprint.pprint(update_key('user_mentions', {'yeah': 'no'}, test))
    # pprint.pprint(test)
    test = [[{'foo': 'bar'}, {'test': 'me'}],
            [{'as': 'we', 'rode': 'on'}, {'foo': 'bar'}]]

    print(flatten(test))
