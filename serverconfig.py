"""Small module to get information from the server config

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import yaml


def get_valid_emails():
    """Get iterator for valid email patterns for this instance.
    This is configurable by the webmaster.

    :returns: List of valid email patterns
    :rtype: list
    """

    emails = []

    with open('keys/valid_email.txt', 'r') as email_file:
        for valid_email in email_file.readlines():
            emails.append(valid_email.strip())

    return emails


def config_dict():
    """
    :returns: the configuration in a dict
    :rtype: str
    """
    with open('keys/config.yml', 'r') as config:
        output = yaml.load(config)

    return output


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
