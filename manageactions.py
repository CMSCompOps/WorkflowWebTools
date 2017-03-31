# pylint: disable=too-many-locals

"""Module to manage actions of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import json
import glob
import sqlite3

from datetime import datetime
from datetime import timedelta

import cherrypy

from . import reasonsmanip
from .globalerrors import check_session

ACTIONS_DIRECTORY = 'actions'
"""The location to store the actions JSON files"""

def extract_reasons_params(action, **kwargs):
    """Extracts the reasons and parameters for an action from kwargs

    :param str action: The action being asked for by the operator
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

            if long_re:
                short_re = item or '---- No Short Reason Given, Not Saved to Database! ----'

                reasons.append({
                    'short': short_re,
                    'long': long_re,
                })

        elif 'selectedreason' in key:

            selectedlist = item if isinstance(item, list) else [item]

            for short in selectedlist:
                if short != "none":
                    notupdate.append({
                        'short': short,
                        'long': old_reasons[short],
                    })

        elif 'param_' in key:
            parameter = '_'.join(key.split('_')[2:])

            if action == 'recover':
                default = 'AllSteps' if parameter != 'sites' else 'Ban'
                which_task = kwargs.get('task_%s' % key.split('_')[1], default)

                if not params.get(which_task):
                    params[which_task] = {}

                params[which_task].update({parameter: item})

            else:
                params[parameter] = item

    reasonsmanip.update_reasons(reasons)

    return reasons + notupdate, params


def submitaction(user, workflows, action, session=None, **kwargs):
    """Writes the action to Unified and notifies the user that this happened

    :param str user: is the user that submitted the action
    :param str workflows: is the original workflow name or workflows
    :param str action: is the suggested action for Unified to take
    :param cherrypy.Session session: the current session
    :param kwargs: can include various reasons and additional datasets
    :returns: a tuple of workflows, reasons, and params for the action
    :rtype: list, str, list of dicts, dict
    """

    reasons, params = extract_reasons_params(action, **kwargs)

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
        wf_params = dict(params)
        step_list = check_session(session).get_step_list(workflow)
        short_step_list = ['/'.join(step.split('/')[2:]) for step in step_list]
        # For recovery, get the proper sites and parameters out for each step
        if action == 'recover':
            all_steps = wf_params.pop('AllSteps', {})
            banned_sites = wf_params.pop('Ban', {'sites': []})['sites']

            # Fill empty parameters for each step from AllSteps
            for short_step_name, step_name in zip(short_step_list, step_list):
                # Get any existing thing (most likely not there)
                step_params = wf_params.get(short_step_name, {})

                for key, val in all_steps.iteritems():
                    # This also includes if the key value is set but blank
                    if not step_params.get(key):
                        step_params[key] = val

                wf_params[short_step_name] = step_params

                # Set the sites
                if kwargs.get('method', 'Manual') != 'Manual':
                    # Banned sites would show up under 'AllSteps'
                    wf_params[short_step_name]['sites'] = \
                        [site for site in \
                             check_session(session).get_workflow(workflow).\
                             site_to_run(step_name) if site not in banned_sites]

        # Only keep the workflow parameters with steps that occur in given workflow
        wf_params = {key: wf_params[key] for key in wf_params \
                         if key in short_step_list}

        add_to_json[workflow] = {
            'Action': action,
            'Parameters': wf_params,
            'Reasons': [reason['long'] for reason in reasons]
            }

    with open(output_file_name, 'w') as outputfile:
        json.dump(add_to_json, outputfile)

    return workflows, reasons, params


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
                    value['user'] = match.split('/')[-1].split('_')[0]
                    yield key, value


def get_actions(num_days):
    """Get the recent actions to be act on in dictionary form

    :param int num_days: is the number of days to check for actions
    :returns: A dictionary of actions, to be rendered as JSON
    :rtype: dict
    """

    output = {}

    conn, curs = get_actions_db()

    for key, value in get_prev_actions(num_days):
        curs.execute('SELECT workflow FROM actions WHERE workflow=?',
                     (key,))
        if not curs.fetchone():
            output[key] = value

    conn.close()

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


def report_actions(workflows):
    """Mark actions as acted on

    :param list workflows: is the list of workflows to no longer show
    """
    conn, curs = get_actions_db()

    for workflow in workflows:
        try:
            curs.execute('INSERT INTO actions VALUES (?)', (workflow,))
        except sqlite3.IntegrityError:
            cherrypy.log('Workflow %s has already been reported' % workflow)

    conn.commit()
    conn.close()


def get_actions_db():
    """Gets the actions database in the local directory.

    :returns: the actions connection, cursor
    :rtype: (sqlite3.Connection, sqlite3.Cursor)
    """

    conn = sqlite3.connect(os.path.join(reasonsmanip.LOCATION, 'actions.db'))
    curs = conn.cursor()
    curs.execute('SELECT name FROM sqlite_master WHERE type="table" and name="actions"')

    if not curs.fetchone():
        curs.execute('CREATE TABLE actions (workflow varchar(255) PRIMARY KEY)')

    return conn, curs
