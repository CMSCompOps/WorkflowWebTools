"""
Small module to get information from the server config.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import os
import sys
import shutil

import yaml


class NoConfig(Exception):
    """
    An exception that is raised if there is no config file
    """
    pass

LOCATION = None

def config_dict():
    """
    :returns: the configuration in a dict
    :rtype: str
    :raises NoConfig: when it cannot find the configuration file
    """

    global LOCATION # pylint: disable=global-statement

    if LOCATION is None:
        if os.path.basename(sys.argv[0]) == 'workflowtool' and len(sys.argv) > 1:
            LOCATION = sys.argv[1]
        else:
            LOCATION = 'config.yml'

    if not os.path.exists(LOCATION):

        default_loc = os.path.join(os.path.dirname(__file__),
                                   'default', 'config.yml')


        if os.path.basename(sys.argv[0]) == 'workflowtool':
            shutil.copy(default_loc, LOCATION)
            sys.tracebacklimit = 0
            raise NoConfig(
                '\n\n  Copied a default configuration to %s.\n  '
                'Please check it, and then run "workflowtool" again.\n'
                % LOCATION)
        else:
            LOCATION = os.path.join(default_loc)

    output = {}

    with open(LOCATION, 'r') as config:
        output = yaml.load(config)

    return output


def get_valid_emails():
    """Get iterator for valid email patterns for this instance.
    This is configurable by the webmaster.

    :returns: List of valid email patterns
    :rtype: list
    """

    valid = config_dict()['valid_emails']

    emails = []
    for domain in valid.get('domains', []):
        emails.append('@' + domain)

    for email in valid.get('whitelist', []):
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


#def host_name():
#    """
#    :returns: the name of the host from the config
#    :rtype: str
#    """
#
#    return config_dict()['host']['name']
#
#
#def host_port():
#    """
#    :returns: the port to host the site on
#    :rtype: str
#    """
#
#    return config_dict()['host']['port']
#
#
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

#def get_cluster_settings():
#    """
#    :returns: dictionary containing the settings for clustering
#    :rtype: dict:
#    """
#
#    return config_dict()['cluster']
#
def get_history_length():
    """
    :returns: the number of days of history to check for workflows
              with an action submitted.
    :rtype: int
    """

    return int(config_dict()['actions']['submithistory'])
