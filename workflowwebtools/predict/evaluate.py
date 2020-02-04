# pylint: disable=missing-docstring, invalid-name, too-many-branches, too-many-locals

"""
A module that evaluates a model and returns the prediction
"""

from __future__ import print_function

import json
import requests

from .. import serverconfig
from ..web.templates import render


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
            requests.get(serverconfig.config_dict()['aieh'],
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
