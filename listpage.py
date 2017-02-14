"""
This module provides lists of workflows/site errors/sites, given the other two values

:author: Daniel Abercrombie
"""


from .globalerrors import list_matching_pievars


def listworkflows(error_code, site_name, session=None):
    """
    Gives back a list of tuples containing workflows and the number of errors
    that matches a given error_code and site_name.

    :param int error_code: The error code that we want workflows for
    :param str site_name: The site name that we want workflows for
    :param cherrypy.Session session: holds the session information
    :returns: List of tuples of workflows and errors, sorted by number of errors
    :rtype: list
    """

    output_dict = {}

    for step, numerrors in list_matching_pievars('stepname', error_code, site_name, session):
        workflow = step.split('/')[1]
        output_dict[workflow] = output_dict.get(workflow, 0) + numerrors

    return sorted(output_dict.items(), key=lambda x: x[1], reverse=True)
