# pylint: disable=redefined-builtin

"""
Here is the list of recommended procedures for various exit codes:

%s

The module :py:mod:`WorkflowWebTools.procedures`, which is used by
:py:mod:`WorkflowWebTools.classifyerrors` contains only the ``PROCEDURES`` dictionary.
The keys of this dictionary are the integer exit codes from the agent to act on.
The values are dictionaries that contain ``'normal'`` and
``'additional'`` actions and a ``'cause'``.
The ``'additional'`` actions are dictionaries containing ``'re'`` and ``'action'``.
The ``'re'`` field is a compiled regular expression to match to the logs.
``group(1)`` of this regular expression is taken to be a parameter to be displayed to the operator.
The ``'action'`` field gives additional instructions to the operator,
who should inspect the parameters returned by the regular expression to determine
the ultimate action to perform.
The ``'cause'`` will add some insight into the error codes in the documentation.
It isn't shown to the operator because they already see the different types of error codes
and are provided with a link to look at the error logs directly.

An example procedure with just exit code ``84`` would look like the following::

    PROCEDURES = {
        84: {
            'normal': 'ACDC',
            'cause': 'The file could not be found',
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

These dictionaries are used to generate the procedures table above.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import re
import textwrap

from tabulate import tabulate

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
        'cause': 'The file could not be found',
        'additional': {
            're': re.compile(r'(root://[-/\w\.]+\.root)'),
            'action': ('If a second round of ACDC and fails for same files, '
                       'contact the transfer team and/or site support team.')
            }
        },
    85: {
        'normal': 'ACDC',
        'cause': ('If FileReadError, the file could not be read. |br| |br| '
                  'If R__unzip: error, most likely a bad node with corrupted '
                  'intermediate files.'),
        'additional': {
            're': re.compile(r'(root://[-/\w\.]+\.root|R__unzip)'),
            'action': ('If getting unzip errors, most likely a bad node. '
                       'Report immediately. |br| |br| '
                       'If a second round of ACDC and fails for same files, '
                       'contact the transfer team and/or site support team.')
            }
        },
    92: {
        'normal': 'ACDC',
        'cause': 'File was not found and fallback procedure also failed.',
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
        'normal': 'Point SSP. Open GGUS ticket and put site in drain.',
        'cause': 'Likely an unrelated batch system kill. Sometimes a site-related problem.'
        },
    99109: {
        'normal': ('Check the Site Readiness and consult with the Site Support Team. |br| |br| '
                   'If a temporary failure: ACDC. |br| |br| '
                   'If a problem with the site: Make GGUS ticket, put the site in drain '
                   'then kill and clone'),
        'cause': 'Uncaught exception in WMAgent step executor (often staging out problems)'
        },
    8004: {
        'normal': 'Report immediately to the Site Support Team.',
        'cause': 'BadAlloc - memory exhaustion'
        },
    11003: {
        'normal': 'ACDC',
        'cause': 'JobExtraction failures'
        },
    73: {
        'normal': 'Open a GitHub issue',
        'cause': ('RootEmbeddedFileSequence: secondary file list seems to be missing. |br| |br| '
                  'When overflow procedure is enables, the agent should be able to see the '
                  'secondary file set as present at those sites as well.')
        },
    50660: {
        'normal': 'More memory',
        'cause': 'Performance kill: "Job exceeding maxRSS"'
        },
    71304: {
        'normal': 'ACDC',
        'cause': 'Job was killed by WMAgent for using too much wallclock time'
        },
    71305: {
        'normal': 'ACDC',
        'cause': 'Job was killed by WMAgent for using too much wallclock time'
        },
    71306: {
        'normal': 'ACDC',
        'cause': 'Job was killed by WMAgent for using too much wallclock time'
        },
    61202: {
        'normal': 'If temporary failure: ACDC, otherwise contact glideinWMS team',
        'cause': 'Can\'t determine proxy filename. X509 user proxy required for job.'
        },
    50513: {
        'normal': 'ACDC',
        'cause': 'Failure to run SCRAM setup scripts'
        },
    99303: {
        'normal': 'Strong failure, report immediately',
        'cause': ('The agent has not found the JobReport.x.pkl file. '
                  'Regardless of the status of the job, it will fail the job with 99303. '
                  'Work is needed to make this error as rare as possible since there '
                  'are very limited cases to make the file fail to appear.')
        },
    8001: {
        'normal': 'Strong failure, report immediately'
        },
    8002: {
        'normal': 'Strong failure, report immediately'
        },
    71104: {
        'normal': ('Copy input files from tape (?) or '
                   'wait for site listed to come out of drain.'),
        'cause': 'Site containing only available copy of input datasets is in drain.',
        'additional': {
            're': re.compile(r'The job can run only at .*(T[12].*)')
            }
        }
    }

# Here is a list comprehension to make you cry.
# I'm basically trying to insert line breaks into the long fields,
# while reseting textwrap's counts at manual line breaks

WRAP = lambda text: ' |br| '.join(
    [' |br| '.join(textwrap.wrap(line, 25)) \
         for line in text.split(' |br| ')]
    )

__doc__ %= tabulate(
    [
        [key,
         WRAP(item.get('cause', '')),
         WRAP(item['normal']),
         WRAP(item.get('additional', {}).get('action', '')),
         ' |br| '.join(item['additional']['re'].pattern.strip('()').split('|')) \
             if item.get('additional', {}).get('re') else '',
        ] \
            for key, item in sorted(PROCEDURES.items(), key=lambda x: x[0])],
    headers=['Exit |br| Code', 'Cause', 'Normal Procedure',
             'Additional Procedure', 'Additional Match |br| Expression'],
    tablefmt='grid'
)
