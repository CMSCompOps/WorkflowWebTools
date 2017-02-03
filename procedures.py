
"""
The module :py:mod:`WorkflowWebTools.procedures`, which is used by
:py:mod:`WorkflowWebTools.classifyerrors` contains only the ``PROCEDURES`` dictionary.
The keys of this dictionary are the integer exit codes from the agent to act on.
The values are dictionaries that contain ``'normal'`` and ``'additional'`` actions.
The ``'additional'`` actions are dictionaries containing ``'re'`` and ``'action'``.
The ``'re'`` field is a compiled regular expression to match to the logs.
``group(1)`` of this regular expression is taken to be a parameter to pass back to the operator.
The ``'action'`` field gives additional instructions to the operator,
who should inspect the parameters returned by the regular expression to determine
the ultimate action to perform.

An example procedure with just exit code ``84`` would look like the following::

    PROCEDURES = {
        84: {
            'normal': 'ACDC',
            'additional': {
                're': re.compile(r'(root://.+root)'),
                'action': ('If a second round of ACDC and fails for same files, '
                           'contact the transfer team and/or site support team.')
                }
            }
        }

What this means is that error code 84 usually should be an ACDC.
However, if the operator sees the same files appear from the regular expression,
then the operator should contact the transfer team and/or the site support team.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import re

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
