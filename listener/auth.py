
import os
import yaml

from constants import THIS_DIR

from tweepy import OAuthHandler


def get_auth_handler():
    with open(os.path.join(THIS_DIR, 'auth.yaml'), 'r') as stream:
        auth_dict = yaml.load(stream)
    auth_handler = OAuthHandler(auth_dict['consumer_key'], auth_dict['consumer_secret'])
    auth_handler.set_access_token(auth_dict['access_token'], auth_dict['access_secret'])
    return auth_handler
