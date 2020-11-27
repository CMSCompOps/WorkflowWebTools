# pylint: disable=missing-docstring, invalid-name, too-many-branches, too-many-locals

"""
A module that evaluates a model and returns the prediction
"""

from __future__ import print_function

import json
import requests

from .. import serverconfig
from ..web.templates import render


def static(workflow):
    """
    Returns the action from the static AIEH model for a given workflow
    :param str workflow: The name of the workflow to check
    :returns: The action determined by the static model
    :rtype: dict
    """
    config = serverconfig.config_dict()

    if config.get('no_predict') or not config.get('aieh'):
        response= {'parameters':{'Action': 0}}
    else:
        response = json.loads(
            requests.get(serverconfig.config_dict()['aieh']['static'],
                         params={'wf': workflow}).text)

    return response


def predict(wf_obj):
    """
    Takes the errors for a workflow and makes an action prediction
    :param workflowwebtool.workflowinfo.WorkflowInfo wf_obj:
        The WorkflowInfo object that we want to perform a prediction on
    :returns: Prediction results to be passed back to a browser
    :rtype: dict
    """

    config = serverconfig.config_dict()

    if config.get('no_predict') or not config.get('aieh'):
        return {'Action': 'Suggestions turned off'}

    wf_name = wf_obj.workflow

    tasks = sorted(wf_obj.get_errors(True).keys())

    table_rows = {
        task: json.loads(
            requests.get(serverconfig.config_dict()['aieh']['models'],
                         params={'wf': wf_name, 'tsk': task}).text)
        for task in tasks}

    # Set of all models turned into a sorted list
    allmodels = table_rows[tasks[0]]

    return {
        'Action': render('predictiontable.html',
                         allmodels=allmodels,
                         tasks=tasks,
                         table_rows=table_rows)
        }
