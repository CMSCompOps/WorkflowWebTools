"""
This module provides lists of errors per pie variable

:author: Daniel Abercrombie
"""


from .globalerrors import list_matching_pievars
from .globalerrors import check_session


def listworkflows(error_code, site_name, workflow, session=None):
    """
    Gives back a list of tuples containing pie variables and the number of errors
    that matches a given error_code and site_name.

    :param int error_code: The error code that we want errors for
    :param str site_name: The site name that we want errors for
    :param str workflow: The workflow that we want errors for
    :param cherrypy.Session session: holds the session information
    :returns: List of tuples of pie variable and errors, sorted by number of errors
    :rtype: list
    """

    output_dict = {}

    if not workflow:
        for step, numerrors in list_matching_pievars('stepname', error_code, site_name, session):
            wkf = step.split('/')[1]
            output_dict[wkf] = output_dict.get(wkf, 0) + numerrors

    else:
        # Click on step piechart
        if len(workflow.split('/')) > 1:

            if not error_code:
                pievar = 'errorcode'
                col = site_name
            elif not site_name:
                pievar = 'sitename'
                col = error_code
            else:
                return []

            for key, numerrors in list_matching_pievars(pievar, workflow, col, session):
                output_dict[key] = output_dict.get(key, 0) + numerrors

        else:
            # Click on workflow (not step)
            info = check_session(session)
            if workflow in info.return_workflows():
                nextlist = info.get_step_list(workflow)
            # Otherwise, is hopefully a PrepID
            else:
                nextlist = info.get_prepid(workflow).get_workflows()

            for step in nextlist:
                for key, numerrors in listworkflows(error_code, site_name, step, session):
                    output_dict[key] = output_dict.get(key, 0) + numerrors


    return sorted(output_dict.items(), key=lambda x: x[1], reverse=True)
