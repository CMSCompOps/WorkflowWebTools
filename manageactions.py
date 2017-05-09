# pylint: disable=too-many-locals

"""Module to manage actions of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import time

import cherrypy
import pymongo

from . import serverconfig
from . import reasonsmanip
from .globalerrors import check_session

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

            if action in ['recover', 'recovery']:
                default = 'AllSteps' if parameter != 'sites' else 'Ban'
                which_task = kwargs.get('task_%s' % key.split('_')[1], default)

                params[which_task] = params.get(which_task, {})

                if parameter == 'sites' and not isinstance(item, list):
                    item = [item]

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

    coll = get_actions_collection()

    if not isinstance(workflows, list):
        workflows = [workflows]

    for workflow in workflows:
        wf_params = dict(params)
        step_list = check_session(session).get_step_list(workflow)
        short_step_list = ['/'.join(step.split('/')[2:]) for step in step_list]
        # For recovery, get the proper sites and parameters out for each step
        if action in ['recover', 'recovery']:
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

        document = {
            'Action': action,
            'Parameters': wf_params,
            'Reasons': [reason['long'] for reason in reasons],
            'user': user
            }

        cherrypy.log('About to insert workflow: %s action: %s' % (workflow, document))

        coll.update_one({'workflow': workflow},
                        {'$set':
                             {'timestamp': int(time.time()),
                              'parameters': document,
                              'acted': 0}},
                        upsert=True)

    return workflows, reasons, params


def get_actions(num_days=None, num_hours=24, acted=0):
    """Get the recent actions to be acted on in dictionary form

    :param int num_days: is the number of days to check for actions
    :param int num_hours: can be used instead of num_days for finer granularity.
                          If ``num_days`` is given, ``num_hours`` is ignored.
    :param int acted: Flag (0, 1, or None) for whether to use acted or not
    :returns: A dictionary of actions, to be rendered as JSON
    :rtype: dict
    """

    if num_days is not None:
        num_hours = num_days * 24

    output = {}
    coll = get_actions_collection()

    age_to_compare = int(time.time()) - num_hours * 3600 if num_hours > 0 else 0

    query = {'timestamp': {'$gt': age_to_compare}, 'acted': acted}
    if acted is None:
        query.pop('acted')

    for match in coll.find(query):
        output[match['workflow']] = match['parameters']

    return output


def get_acted_workflows(num_days):
    """Get all of the workflows that have actions assigned

    :param int num_days: is the number of past days to check for actions.
                         This speeds up the check while not losing the
                         ability to look farther back in time.
    :returns: a list of workflows acted on
    :rtype: list
    """

    return list(get_actions(num_days, acted=None))


def report_actions(workflows):
    """Mark actions as acted on

    :param list workflows: is the list of workflows to no longer show
    """
    coll = get_actions_collection()

    coll.update_many({'workflow': {'$in': workflows}, 'acted': 0},
                     {'$set': {'acted': 1}})


def get_actions_collection():
    """Gets the actions collection from MongoDB.

    :returns: the actions collection
    :rtype: pymongo.collection.Collection
    """

    client = pymongo.MongoClient()
    coll = client[serverconfig.config_dict()['actions']['database']].actions

    if coll.count() == 0 or 'workflow' not in list(coll.index_information()):
        coll.create_index([('workflow', pymongo.TEXT)],
                          name='workflow', unique=True)

    return coll


def fix_sites(**kwargs):
    """Fix the site lists for tasks that had zero sites.

    :param kwargs: Keywords to be parsed by :py:func:`extract_reasons_params`
    """

    _, params = extract_reasons_params('recover', **kwargs)

    coll = get_actions_collection()

    for task, value in params.iteritems():
        split_task = task.split('/')
        workflow = split_task[1]
        subtask = '/'.join(split_task[2:])

        output = coll.find_one({'workflow': workflow})['parameters']
        output['Parameters'][subtask]['sites'] = value['sites']

        coll.update_one({'workflow': workflow},
                        {'$set': {'parameters': output}})

    print params
