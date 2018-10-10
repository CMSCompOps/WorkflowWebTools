# pylint: disable=too-many-locals, too-complex

"""Module to manage actions of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import time
import datetime
import ssl

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

    tasks_to_do = kwargs.get('dotasks', [])
    if not isinstance(tasks_to_do, list):
        tasks_to_do = [tasks_to_do]

    for key, item in kwargs.iteritems():

        if 'shortreason' in key:
            short_re = item or reasonsmanip.DEFAULT_SHORT
            long_re = kwargs[key.replace('short', 'long')].strip().replace('\n', '<br>') or item

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

            if action in ['acdc', 'recovery']:
                default = 'AllSteps' if parameter != 'sites' else 'Ban'
                which_task = kwargs.get('task_%s' % key.split('_')[1], default)

                if tasks_to_do and which_task != default \
                        and which_task not in tasks_to_do:
                    continue

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

    cherrypy.log('args: {0}'.format(kwargs))
    dotasks = kwargs.get('dotasks', [])
    if not isinstance(dotasks, list):
        dotasks = [dotasks]

    reasons, params = extract_reasons_params(action, **kwargs)

    cherrypy.log('Parameters: {0}'.format(params))

    coll = get_actions_collection()

    error_info = check_session(session)

    # Let's define some lambdas to use to filter our ACDCs (sanity checks)
    # First a quick shorthand for workflow parameters
    get_params = lambda wkf: error_info.get_workflow(wkf).get_workflow_parameters()

    # We want request type to be resubmission in our ACDC
    is_resub = lambda wkf: \
        get_params(wkf)['RequestType'] == 'Resubmission'

    # We want our ACDC to be submitted after the original request
    is_new = lambda wkf, workflow: \
        datetime.datetime(*(get_params(wkf)['RequestDate'])) > \
        datetime.datetime(*(get_params(workflow)['RequestDate']))


    if not isinstance(workflows, list):
        workflows = [workflows]

    for workflow in workflows:
        wf_params = dict(params)
        step_list = error_info.get_step_list(workflow)
        short_step_list = ['/'.join(step.split('/')[2:]) for step in step_list]
        # For recovery, get the proper sites and parameters out for each step
        if action in ['acdc', 'recovery']:
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
                             if key in short_step_list and \
                             (key in dotasks or not dotasks)}

        document = {
            'Action': action,
            'Parameters': wf_params,
            'Reasons': [reason['long'] for reason in reasons],
            'user': user,
            'ACDCs': [wkf for wkf in error_info.get_prepid(
                error_info.get_workflow(workflow).get_prep_id()).get_workflows() \
                          if wkf != workflow and is_resub(wkf) and is_new(wkf, workflow)]
            }

        cherrypy.log('About to insert workflow: %s action: %s' % (workflow, document))

        coll.update_one({'workflow': workflow},
                        {'$set':
                             {'timestamp': int(time.time()),
                              'parameters': document,
                              'acted': 0}},
                        upsert=True)

    return workflows, reasons, params


def submit2(documents): # pylint: disable=missing-docstring
    coll = get_actions_collection()

    for document in documents:
        workflow = document['workflow']
        params = document['parameters']

        cherrypy.log('About to insert workflow: %s action: %s' % (workflow, params))

        coll.update_one({'workflow': workflow},
                        {'$set':
                             {'timestamp': int(time.time()),
                              'parameters': params,
                              'acted': 0}},
                        upsert=True)


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


def get_datetime_submitted(workflow):
    """Get the datetime for a submitted workflow

    :param str workflow: A workflow to get the time submitted
    :returns: A datetime object, or None if the workflow has never been submitted
    :rtype: datetime.datetime or None
    """

    coll = get_actions_collection()

    info = coll.find_one({'workflow': workflow})
    if info:
        return datetime.datetime.fromtimestamp(info['timestamp'])

    return None


def get_acted_workflows(num_days):
    """Get all of the workflows that have actions assigned

    :param int num_days: is the number of past days to check for actions.
                         This speeds up the check while not losing the
                         ability to look farther back in time.
    :returns: a list of workflows acted on
    :rtype: list
    """

    return list(get_actions(num_days, acted=None))


def report_actions(workflows, output=None):
    """Mark actions as acted on

    :param list workflows: is the list of workflows to no longer show
    :param dict output: If set, a reference to a dictionary to update
                        with details of what was and wasn't set to acted
    """
    coll = get_actions_collection()

    if output is not None:
        records = list(coll.find({'workflow': {'$in': workflows}}))
        output['success'] = [record['workflow'] for record in records
                             if record['acted'] == 0]
        output['already_reported'] = [record['workflow'] for record in records
                                      if record['acted'] != 0]

        record_names = [record['workflow'] for record in records]
        output['does_not_exist'] = [wrkf for wrkf in workflows if
                                    wrkf not in record_names]

    coll.update_many({'workflow': {'$in': workflows}, 'acted': 0},
                     {'$set': {'acted': 1}})


def get_actions_collection():
    """Gets the actions collection from MongoDB.

    :returns: the actions collection
    :rtype: pymongo.collection.Collection
    """

    config_dict = serverconfig.config_dict()['actions']
    uri = config_dict.get('uri')
    if uri:
        client = pymongo.MongoClient(uri, ssl_cert_reqs=ssl.CERT_NONE)
    else:
        client = pymongo.MongoClient()

    coll = client[config_dict['database']].actions

    if coll.count() == 0 or 'workflow' not in list(coll.index_information()):
        coll.create_index([('workflow', pymongo.TEXT)],
                          name='workflow', unique=True)

    return coll


def fix_sites(**kwargs):
    """Fix the site lists for tasks that had zero sites.

    :param kwargs: Keywords to be parsed by :py:func:`extract_reasons_params`
    """

    _, params = extract_reasons_params('acdc', **kwargs)

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
