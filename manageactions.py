"""
Module to manage actions of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import json
from . import reasonsmanip


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


def submitaction(workflows, action, **kwargs):
    """Writes the action to Unified and notifies the user that this happened

    :param str workflows: is the original workflow name or workflows
    :param str action: is the suggested action for Unified to take
    :param kwargs: can include various reasons and additional datasets
    :returns: a tuple of workflows, action, reasons, and params for the action
    :rtype: list, str, list of dicts, dict
    """

    reasons, params = extract_reasons_params(**kwargs)

    output_file_name = 'actions/new_action.json'

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
