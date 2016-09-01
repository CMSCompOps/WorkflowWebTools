"""
Module to manage actions of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import json
import glob


from datetime import datetime
from datetime import timedelta
from . import reasonsmanip


ACTIONS_DIRECTORY = 'actions'
"""The location to store the actions JSON files"""

def extract_reasons_params(**kwargs):
    """Extracts the reasons and parameters for an action from kwargs

    :param kwargs: Keywords that are submitted via POST to /submitaction
    :returns: reasons for action, and parameters for the action
    :rtype: list, dict
    """

    old_reasons = reasonsmanip.reasons_list()
    reasons = []
    notupdate = []
    params = {}

    for key, item in kwargs.iteritems():

        if 'shortreason' in key:
            long_re = kwargs[key.replace('short', 'long')].strip().replace('\n', '<br>')

            if len(long_re) == 0:
                continue

            if item != '':
                reasons.append({
                    'short': item,
                    'long': long_re,
                })
            else:
                notupdate.append({
                    'short': '---- No Short Reason Given, Not Saved to Database! ----',
                    'long': long_re,
                })

        elif 'selectedreason' in key:

            if not isinstance(item, list):
                item = [item]

            for short in item:
                if short != "none":
                    notupdate.append({
                        'short': short,
                        'long': old_reasons[short],
                        })

        elif 'param_' in key:
            parameter = '_'.join(key.split('_')[1:])
            params[parameter] = item

    reasonsmanip.update_reasons(reasons)

    return reasons + notupdate, params


def submitaction(user, workflows, action, **kwargs):
    """Writes the action to Unified and notifies the user that this happened

    :param str user: is the user that submitted the action
    :param str workflows: is the original workflow name or workflows
    :param str action: is the suggested action for Unified to take
    :param kwargs: can include various reasons and additional datasets
    :returns: a tuple of workflows, action, reasons, and params for the action
    :rtype: list, str, list of dicts, dict
    """

    reasons, params = extract_reasons_params(**kwargs)

    if not os.path.exists(ACTIONS_DIRECTORY):
        os.makedirs(ACTIONS_DIRECTORY)

    output_file_name = os.path.join(
        ACTIONS_DIRECTORY, '{0}_{1}.json'.\
            format(user, datetime.now().strftime('%Y%m%d'))
        )

    add_to_json = {}
    if os.path.isfile(output_file_name):
        with open(output_file_name, 'r') as outputfile:
            add_to_json = json.load(outputfile)

    if not isinstance(workflows, list):
        workflows = [workflows]

    for workflow in workflows:
        add_to_json[workflow] = {
            'Action': action,
            'Parameters': params,
            'Reasons': [reason['long'] for reason in reasons]
            }

    with open(output_file_name, 'w') as outputfile:
        json.dump(add_to_json, outputfile)

    return workflows, action, reasons, params


def get_prev_actions(num_days):
    """Get the keys and values of recent actions

    :param int num_days: is the number of days to check for actions
    :rtype: generator
    """

    date = datetime.now()
    date_int = int(date.strftime('%Y%m%d'))
    prev_int = int((date - timedelta(num_days)).strftime('%Y%m%d'))

    for match in glob.iglob(os.path.join(ACTIONS_DIRECTORY, '*.json')):
        check_int = int(match.split('_')[-1].rstrip('.json'))
        if prev_int <= check_int <= date_int:
            with open(match, 'r') as infile:
                output = json.load(infile)
                for key, value in output.iteritems():
                    yield key, value


def get_actions(num_days):
    """Get the recent actions to be act on in dictionary form

    :param int num_days: is the number of days to check for actions
    :returns: A dictionary of actions, to be rendered as JSON
    :rtype: dict
    """

    output = {}

    for key, value in get_prev_actions(num_days):
        output[key] = value

    return output


def get_acted_workflows(num_days):
    """Get all of the workflows that have actions assigned

    :param int num_days: is the number of past days to check for actions.
                         This speeds up the check while not losing the
                         ability to look farther back in time.
    :returns: a list of workflows acted on
    :rtype: list
    """

    workflows = []

    for key, _ in get_prev_actions(num_days):
        workflows.append(key)

    return workflows
