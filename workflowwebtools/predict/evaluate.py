# pylint: disable=missing-docstring, invalid-name, too-many-branches, too-many-locals

"""
A module that evaluates a model and returns the prediction
"""

from __future__ import print_function

import requests

from .. import serverconfig


def predict(wf_obj):
    """
    Takes the errors for a workflow and makes an action prediction
    :param workflowwebtool.workflowinfo.WorkflowInfo wf_obj:
        The WorkflowInfo object that we want to perform a prediction on
    :returns: Prediction results to be passed back to a browser
    :rtype: dict
    """

    if serverconfig.config_dict().get('no_predict'):
        return {'Action': 'Suggestions turned off'}

    wf_name = wf_obj.workflow

    tasks = sorted(wf_obj.get_errors(True).keys())

    return {
        'Action': '\n<ul>\n<li>' + '\n<li>'.join([
            task + '<br>' +
            requests.get(serverconfig.config_dict()['aieh'],
                         params={'wf': wf_name, 'tsk': task}).text
            for task in tasks]) + '\n</ul>'
    }
