"""Small module to get information from the server config.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import os
import logging

import yaml


def config_dict():
    """
    :returns: the configuration in a dict
    :rtype: str
    """
    logging.info('Attempting to load configuration')
    location = 'keys/config.yml'
    output = {}
    if os.path.exists(location):
        with open(location, 'r') as config:
            output = yaml.load(config)
    else:
        logging.critical('Could not load config at %s', location)

    return output


CONFIG_DICT = config_dict()
"""Config loaded on the first import"""


def get_valid_emails():
    """Get iterator for valid email patterns for this instance.
    This is configurable by the webmaster.

    :returns: List of valid email patterns
    :rtype: list
    """

    emails = []

    location = 'keys/valid_email.txt'
    if os.path.exists(location):
        with open(location, 'r') as email_file:
            for valid_email in email_file.readlines():
                emails.append(valid_email.strip())
    else:
        logging.error('Could not load config at %s', location)

    return emails


def wm_email():
    """
    :returns: the email of the webmaster
    :rtype: str
    """

    return CONFIG_DICT['webmaster']['email']


def wm_name():
    """
    :returns: the name of the webmaster
    :rtype: str
    """

    return CONFIG_DICT['webmaster']['name']


def host_name():
    """
    :returns: the name of the host from the config
    :rtype: str
    """

    return CONFIG_DICT['host']['name']


def host_port():
    """
    :returns: the port to host the site on
    :rtype: str
    """

    return CONFIG_DICT['host']['port']


def workflow_history_path():
    """
    :returns: the path to the files of workflow error history
    :rtype: str
    """

    return CONFIG_DICT['data']['workflow_history']
