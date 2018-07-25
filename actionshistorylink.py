"""
The :py:mod:`actionshistorylink` module creates files that link
the action and the errors thrown for each task where the action and history
are both stored on the server.
The ``config.yml`` file is read to determine the locations of this history databases.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import json

from . import serverconfig
from . import manageactions
from . import globalerrors


def dump_json(file_name=None):
    """
    Dump a list of pairs into a file and returns the dictionary.
    The pairs are dictionary of errors, and action document.
    Each element in the list corresponds to a different subtask.

    :param str file_name: The location to place the json file, if set
    :returns: The errors and actions for each subtask
    :rtype: dict
    """

    output = {}

    history = globalerrors.ErrorInfo(serverconfig.workflow_history_path())
    actions = manageactions.get_actions(0, acted=None)

    session = {'info': history}

    for workflow in actions:
        for subtask in history.get_step_list(workflow):
            if actions[workflow]['Action'] in ['acdc', 'recovery']:
                parameters = actions[workflow]['Parameters'].get(
                    '/'.join(subtask.split('/')[2:]), {})
            else:
                parameters = actions[workflow]['Parameters']

            output[subtask] = {
                'errors': {
                    'good_sites': globalerrors.get_step_table(
                        subtask, session, readymatch=['green'],
                        sparse=True),
                    'bad_sites': globalerrors.get_step_table(
                        subtask, session, readymatch=['yellow', 'red', 'none'],
                        sparse=True)
                    },
                'parameters':
                    parameters
                }
            output[subtask]['parameters']['action'] = actions[workflow]['Action']

    if file_name:
        with open(file_name, 'w') as output_file:
            json.dump(output, output_file)

    return output
