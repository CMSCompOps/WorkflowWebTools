"""Small module to get information from the server config.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import os

import yaml


LOCATION = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test')
"""The string giving the location that serverconfig looks first for the configuration"""

def config_dict():
    """
    :returns: the configuration in a dict
    :rtype: str
    :raises Exception: when it cannot find the configuration file
    """

    file_name = 'config.yml'
    location = os.path.join(LOCATION, file_name)
    output = {}

    # If not local, check the runserver directory
    if not os.path.exists(location):
        location = os.path.join(os.path.dirname(__file__),
                                'runserver', file_name)

    # If not there, fall back to the test directory
    if not os.path.exists(location):
        location = os.path.join(os.path.dirname(__file__),
                                'test', file_name)

    if os.path.exists(location):
        with open(location, 'r') as config:
            output = yaml.load(config)
    else:
        raise Exception('Could not load config at ' + os.path.join(LOCATION, file_name))

    return output


def get_valid_emails():
    """Get iterator for valid email patterns for this instance.
    This is configurable by the webmaster.

    :returns: List of valid email patterns
    :rtype: list
    """

    emails = []
    for domain in config_dict()['valid_emails'].get('domains', []):
        emails.append('@' + domain)

    for email in  config_dict()['valid_emails'].get('whitelist', []):
        emails.append(email)

    return emails


def wm_email():
    """
    :returns: the email of the webmaster
    :rtype: str
    """

    return config_dict()['webmaster']['email']


def wm_name():
    """
    :returns: the name of the webmaster
    :rtype: str
    """

    return config_dict()['webmaster']['name']


def host_name():
    """
    :returns: the name of the host from the config
    :rtype: str
    """

    return config_dict()['host']['name']


def host_port():
    """
    :returns: the port to host the site on
    :rtype: str
    """

    return config_dict()['host']['port']


def workflow_history_path():
    """
    :returns: the path to the files of workflow error history
    :rtype: str
    """

    return config_dict()['data']['workflow_history']

def all_errors_path():
    """
    :returns: the path to all errors for recent workflows
    :rtype: str
    """

    return config_dict()['data']['all_errors']

def get_cluster_settings():
    """
    :returns: dictionary containing the settings for clustering
    :rtype: dict:
    """

    return config_dict()['cluster']

def get_history_length():
    """
    :returns: the number of days of history to check for workflows
              with an action submitted.
    :rtype: int
    """

    return int(config_dict()['actions']['submithistory'])
