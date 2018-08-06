"""
This module reads the explain error info for a session and tries to
classify them in a way that can help recommend procedures to the operator.
These procedures are gathered from :py:mod:`WorkflowWebTools.procedures`.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import re

from .procedures import PROCEDURES
from .globalerrors import check_session

def classifyerror(errorcode, workflow, session=None):
    """
    Return the most relevant characteristics of an error code for this session.
    This will include things like:

    - Files not opening
    - StageOut errors

    .. Note::

       More error types should be added to this function as needed

    :param int errorcode: The error code that we want to classify
    :param str workflow: the workflow that we want to get the errors from
    :param cherrypy.Session session: Is the user's cherrypy session
    :returns: A tuple of strings describing the key characteristics of the errorcode.
              These strings are good for printing directly in web browsers.
              The first string is the types of errors reported with this error code.
              The second string is the recommended normal actions.
              The third string contains special parameters useful for additional actions.
    :rtype: str, str, str
    """

    procedure = PROCEDURES.get(errorcode, {})

    logs = check_session(session).get_workflow(workflow).get_explanation(str(errorcode))

    error_re = re.compile(r'[\w\s]+ \(Exit code: (\d+)\)')
    error_types = {}

    additional_re = procedure.get('additional', {}).get('re', None)
    additional_params = []

    for log in logs:
        for line in log.split('\n'):
            # Add each type of error associated with the log
            match = error_re.match(line)
            if match and match.group(1) not in error_types.keys():
                error_types[match.group(1)] = match.group(0)
            # Get additional parameters

            if '.root' not in line:
                continue

            if additional_re:
                add_match = additional_re.search(line)
                if add_match and add_match.group(1) not in additional_params:
                    additional_params.append(add_match.group(1))

    # Create the strings to return

    error_types_string = '<br>'.join([error_types[key] for key in \
                                          sorted(error_types.keys(), key=int)])

    normal_action_string = procedure.get('normal', 'No instructions for this error code')

    additional_actions_string = '<br>'.join(
        [PROCEDURES[errorcode].get('additional', {}).get('action', ''), 'Problems:'] +
        additional_params) if additional_params else ''

    # The procedures use ' |br| |br| ' to break lines because sphinx uses that
    # to replace with raw html

    return (error_types_string,
            normal_action_string.replace(' |br| |br| ', '<br>'),
            additional_actions_string.replace(' |br| |br| ', '<br>'))


def get_max_errorcode(workflow, session=None):
    """
    Get the errorcode with the most errors for a session

    :param str workflow: Is the primary name of the workflow
    :param cherrypy.Session session: Is the user's cherrypy session
    :returns: The error code that appears most often for this workflow
    :rtype: int
    """


    curs, _, allerrors, _ = check_session(session).info

    num_errors = []

    for errorcode in allerrors:
        output = curs.execute("SELECT SUM(numbererrors) FROM workflows WHERE "
                              "stepname LIKE '/{0}/%' AND errorcode={1}".\
                                  format(workflow, errorcode))

        num_errors.append(output[0])

    return allerrors[num_errors.index(max(num_errors))]
