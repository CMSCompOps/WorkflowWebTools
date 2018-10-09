#pylint: disable=missing-docstring

import os
import json
import urlparse

from cmstoolbox.webtools import get_json

from workflowwebtools import serverconfig

def open_statuses(location):
    if os.path.isfile(location):
        with open(location, 'r') as input_file:
            return json.load(input_file)

    components = urlparse.urlparse(location)
    cookie_stuff = serverconfig.config_dict()['data']

    return get_json(components.netloc, components.path,
                    use_https=True,
                    cookie_file=cookie_stuff.get('cookie_file'),
                    cookie_pem=cookie_stuff.get('cookie_pem'),
                    cookie_key=cookie_stuff.get('cookie_key'))


def get_manual_workflows(location):
    """
    :param str location: Either the file location or the URL of statuses.json
    :returns: list of workflows in manual assistance
    :rtype: list
    """

    return [workflow for workflow, statuses
            in open_statuses(location).iteritems()
            if True in ['manual' in status for status in statuses]]
