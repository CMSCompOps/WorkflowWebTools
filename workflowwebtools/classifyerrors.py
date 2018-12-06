"""
This module reads the explain error info for a session and tries to
classify them in a way that can help recommend procedures to the operator.
These procedures are gathered from :py:mod:`WorkflowWebTools.procedures`.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import re

from collections import defaultdict

from .procedures import PROCEDURES

def classifyerror(errorcode, workflow):
    """
    Return the most relevant characteristics of an error code for this session.
    This will include things like:

    - Files not opening
    - StageOut errors

    .. Note::

       More error types should be added to this function as needed

    :param int errorcode: The error code that we want to classify
    :param workflowinfo.WorkflowInfo workflow: the workflow that we want to get the errors from
    :returns: A tuple of strings describing the key characteristics of the errorcode.
              These strings are good for printing directly in web browsers.
              The first string is the types of errors reported with this error code.
              The second string is the recommended normal actions.
              The third string contains special parameters useful for additional actions.
    :rtype: str, str, str
    """

    procedure = PROCEDURES.get(errorcode, {})

    logs = workflow.get_explanation(str(errorcode))

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


def get_max_errorcode(workflow):
    """
    Get the errorcode with the most errors for a session

    :param workflowinfo.WorkflowInfo workflow: the workflow that we want to get the errors from
    :returns: The error code that appears most often for this workflow
    :rtype: int
    """

    errors = workflow.get_errors(True)
    errors_summed = defaultdict(int)

    for codes in errors.values():
        for errorcode, sites in codes.items():
            numcode = -1 if errorcode == 'NotReported' else int(errorcode)
            for num in sites.values():
                errors_summed[numcode] += num

    output = 0
    max_num = 0
    for code, num in errors_summed.items():
        if num > max_num:
            max_num = num
            output = code

    return output
