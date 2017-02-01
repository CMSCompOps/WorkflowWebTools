"""
This module reads the explain error info for a session and tries to
classify them in a way that can help recommend procedures to the operator.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import re

from .globalerrors import check_session

#
# These are the procedures listed on the WTC twiki:
# https://twiki.cern.ch/twiki/bin/view/CMS/CompOpsPRWorkflowTrafficController#Error_Codes_Mapping
# The normal procedure for each error code is listed
# Additional procedures take into account some parameters
# The parameters are extracted into group(1) of the regular expressions
#
PROCEDURES = {
    84: {
        'normal': 'ACDC',
        'additional': {
            're': re.compile(r'(root://[-/\w\.]+\.root)'),
            'action': ('If a second round of ACDC and fails for same files, '
                       'contact the transfer team and/or site support team.')
            }
        },
    95: {
        'normal': 'ACDC',
        'additional': {
            're': re.compile(r'(root://[-/\w\.]+\.root|R__unzip)'),
            'action': ('If getting unzip errors, most likely a bad node. '
                       'Report immediately.<br>'
                       'If a second round of ACDC and fails for same files, '
                       'contact the transfer team and/or site support team.')
            }
        },
    92: {
        'normal': 'ACDC',
        'additional': {
            're': re.compile(r'(root://[-/\w\.]+\.root)'),
            'action': ('If a second round of ACDC and fails for same files, '
                       'contact the transfer team and/or site support team.')
            }
        },
    134: {
        'normal': 'Strong failure to report immediately'
        },
    137: {
        'normal': 'Point SSP. Open GGUS ticket and put site in drain.'
        },
    99109: {
        'normal': ('Check the Site Readiness and consult with the Site Support Team.<br>'
                   'If a temporary failure: ACDC.<br>'
                   'If a problem with the site: Make GGUS ticket, put the site in drain '
                   'then kill and clone')
        },
    8004: {
        'normal': 'Report immediately to the Site Support Team.'
        },
    11003: {
        'normal': 'ACDC'
        },
    73: {
        'normal': 'Open a GitHub issue'
        },
    50660: {
        'normal': 'More memory'
        },
    71304: {
        'normal': 'ACDC'
        },
    71305: {
        'normal': 'ACDC'
        },
    71306: {
        'normal': 'ACDC'
        },
    61202: {
        'normal': 'If temporary failure: ACDC, otherwise contact glideinWMS team'
        },
    50513: {
        'normal': 'ACDC'
        },
    99303: {
        'normal': 'Strong failure, report immediately'
        },
    8001: {
        'normal': 'Strong failure, report immediately'
        },
    8002: {
        'normal': 'Strong failure, report immediately'
        },
    }

def classifyerror(errorcode, session=None):
    """
    Return the most relevant characteristics of an error code for this session.
    This will include things like:

    - Files not opening
    - StageOut errors

    .. Note::

       More error types should be added to this function as needed

    :param int errorcode: The error code that we want to classify
    :param cherrypy.Session session: the current session
    :returns: A tuple of strings describing the key characteristics of the errorcode.
              These strings are good for printing directly in web browsers.
              The first string is the types of errors reported with this error code.
              The second string is the recommended normal actions.
              The third string contains special parameters useful for additional actions.
    :rtype: str, str
    """

    procedure = PROCEDURES.get(errorcode, {})

    logs = check_session(session).get_errors_explained().\
        get(str(errorcode), [])

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
                print 'Checking add'
                add_match = additional_re.search(line)
                print add_match
                print add_match is None
                if add_match and add_match.group(1) not in additional_params:
                    additional_params.append(add_match.group(1))

    # Create the strings to return

    error_types_string = '<br>'.join([error_types[key] for key in \
                                          sorted(error_types.keys(), key=int)])

    normal_action_string = procedure.get('normal', 'No instructions for this error code')

    additional_actions_string = '<br>'.join(
        [PROCEDURES[errorcode].get('additional', {}).get('action', ''), 'Problems:'] +
        additional_params) if additional_params else ''

    return (error_types_string, normal_action_string, additional_actions_string)


def get_max_errorcode(workflow, session=None):
    """
    Get the errorcode with the most errors for a session

    :param str workflow: Is the primary name of the workflow
    :param cherrypy.Session session: Is the user's cherrypy session
    :returns: The error code that appears most often for this workflow
    :rtype: int
    """


    curs, _, allerrors, _, _ = check_session(session).info

    num_errors = []

    for errorcode in allerrors:
        curs.execute("SELECT SUM(numbererrors) FROM workflows WHERE "
                     "stepname LIKE '/{0}/%' AND errorcode={1}".\
                         format(workflow, errorcode))
        output = curs.fetchall()

        num_errors.append(output[0])

    return allerrors[num_errors.index(max(num_errors))]
