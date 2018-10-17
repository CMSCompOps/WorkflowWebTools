"""
Module containing and returning information about workflows.

:authors: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import re
import json
import time
import datetime
import threading

from collections import defaultdict
from functools import wraps

from cmstoolbox.webtools import get_json
from cmstoolbox.sitereadiness import site_list

from . import serverconfig

def cached_json(attribute, timeout=None):
    """
    A decorator for caching dictionaries in local files.

    :param str attribute: The key of the :py:class:`WorkflowInfo` cache to
                          set using the decorated function.
    :param int timeout: The amount of time before refreshing the JSON file, in seconds.
    :returns: Function decorator
    :rtype: func
    """

    def cache_decorator(func):
        """
        The actual decorator (since decorator takes an argument)

        :param func func: A function to modify
        :returns: Decorated function
        :rtype: func
        """

        @wraps(func)
        def function_wrapper(self, *args, **kwargs):
            """
            Executes the :py:class:`WorkflowInfo` function

            :returns: Output of the originally decorated function
            :rtype: dict
            """
            tmout = timeout or serverconfig.config_dict()['cache_refresh'].get(attribute)

            if not os.path.exists(self.cache_dir):
                os.mkdir(self.cache_dir)

            self.cachelock.acquire()
            if attribute not in self.cachelocks:
                self.cachelocks[attribute] = threading.Lock()

            self.cachelocks[attribute].acquire()
            self.cachelock.release()

            check_var = self.cache.get(attribute)

            if check_var is None:
                file_name = self.cache_filename(attribute)
                if os.path.exists(file_name) and \
                        (tmout is None or time.time() - tmout < os.stat(file_name).st_mtime):
                    try:
                        with open(file_name, 'r') as cache_file:
                            check_var = json.load(cache_file)
                    except ValueError:
                        print 'JSON file no good. Deleting %s. Try again later.' % file_name
                        os.remove(file_name)

                # If still None, call the wrapped function
                if check_var is None:
                    check_var = func(self, *args, **kwargs)
                    with open(file_name, 'w') as cache_file:
                        json.dump(check_var, cache_file)

                self.cache[attribute] = check_var

            self.cachelocks[attribute].release()

            return check_var or {}

        return function_wrapper

    return cache_decorator


def list_workflows(status):
    """
    Get the list of workflows currently in a given status.
    For a list of valid requests, visit the
    `Request Manager Interface <https://cmsweb.cern.ch/reqmgr2/>`_.

    :param str status: The status of the workflow lists being looked for
    :returns: A list of workflows matching the status
    :rtype: list
    """

    request = get_json('cmsweb.cern.ch', '/reqmgr2/data/request',
                       params={'status': status, 'detail': 'false'},
                       use_cert=True)

    return request['result']


def errors_for_workflow(workflow, url='cmsweb.cern.ch'):
    """
    Get the useful status information from a workflow

    :param str workflow: the name of the workflow request
    :param str url: the base url to find the information at
    :returns: a dictionary containing error codes in the following format::

              {step: {errorcode: {site: number_errors}}}

    :rtype: dict
    """

    result = get_json(url,
                      '/wmstatsserver/data/jobdetail/%s' % workflow,
                      use_cert=True)

    output = {}

    if not result['result']:
        return output

    for step, stepdata in result['result'][0].get(workflow, {}).iteritems():
        errors = {}
        for code, codedata in stepdata.get('jobfailed', {}).iteritems():
            sites = {}
            for site, sitedata in codedata.iteritems():
                if sitedata['errorCount']:
                    sites[site] = sitedata['errorCount']

            if sites:
                errors[code] = sites

        if errors:
            output[step] = errors

    return output


def explain_errors(workflow, errorcode):
    """
    Get example errors for a given workflow and errorcode

    :param str workflow: is the workflow name
    :param str errorcode: is the error code
    :returns: a dict of log snippets from different sites.
    :rtype: list
    """

    result = get_json('cmsweb.cern.ch',
                      '/wmstatsserver/data/jobdetail/%s' % workflow,
                      use_cert=True)

    output = []

    if not result['results']:
        return output

    for stepdata in result['result'][0].get(workflow, {}).values():
        for sitedata in stepdata.get('jobfailed', {}).get(errorcode, {}).values():
            for samples in sitedata['samples'][0]['errors'].values():

                output.extend(samples)

    return output


class Info(object):
    """
    Implements shared operations on the cache
    """

    def __init__(self):
        # Stores things using the cached_json decorator
        self.cache = {}
        self.cache_dir = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'workflowinfo')
        self.bak_dir = os.path.join(self.cache_dir, 'bak')
        self.cachelock = threading.Lock()
        self.cachelocks = {}

    def __str__(self):
        pass

    def cache_filename(self, attribute):
        """
        Return the name of the file for caching

        :param str attribute: The information to store in the file
        :returns: The full file name to store the cache
        :rtype: str
        """
        return os.path.join(self.cache_dir, '%s_%s.cache.json' % (self, attribute))

    def reset(self):
        """
        Reset the cache for this object and clear out the files.
        """
        print 'Reseting %s' % self

        if not os.path.exists(self.bak_dir):
            os.mkdir(self.bak_dir)

        for attribute in self.cache:
            cache_file = self.cache_filename(attribute)
            if os.path.exists(cache_file):
                os.rename(cache_file, cache_file.replace(self.cache_dir, self.bak_dir))

        self.cache.clear()


class WorkflowInfo(Info):
    """
    Class that holds methods for accessing various information about a workflow.
    """

    def __init__(self, workflow, url='cmsweb.cern.ch'):
        """
        Initialize the workflow info class

        :param str workflow: is the name of the workflow
        :param str url: is the url to fetch information from
        """

        super(WorkflowInfo, self).__init__()
        self.workflow = workflow
        self.url = url

        # Is set first time get_explanation() is called
        self.explanations = None

    def __str__(self):
        return 'workflowinfo_%s' % self.workflow

    @cached_json('workflow_params')
    def get_workflow_parameters(self):
        """
        Get the workflow parameters from ReqMgr2, or returns a cached value.
        See the `ReqMgr 2 wiki <https://github.com/dmwm/WMCore/wiki/reqmgr2-apis>`_
        for more details.

        :returns: Parameters for the workflow from ReqMgr2.
        :rtype: dict
        """

        try:
            result = get_json(self.url,
                              '/reqmgr2/data/request',
                              params={'name': self.workflow},
                              use_https=True, use_cert=True)

            for params in result['result']:
                for key, item in params.iteritems():
                    if key == self.workflow:
                        return item

        except Exception as error:
            print 'Failed to get from reqmgr', self.workflow
            print str(error)

        return None


    @cached_json('errors')
    def get_errors(self, get_unreported=False):
        """
        A wrapper for :py:func:`errors_for_workflow` if you happen to have
        a :py:class:`WorkflowInfo` object already.

        :param bool get_unreported: Get the unreported errors from ACDC server
        :returns: a dictionary containing error codes in the following format::

                  {step: {errorcode: {site: number_errors}}}

        :rtype: dict
        """

        output = errors_for_workflow(self.workflow, self.url)

        if get_unreported:
            acdc_server_response = get_json(
                'cmsweb.cern.ch', '/couchdb/acdcserver/_design/ACDC/_view/byCollectionName',
                {'key': '"%s"' % self.workflow, 'include_docs': 'true', 'reduce': 'false'},
                use_cert=True)

            for row in acdc_server_response['rows']:
                task = row['doc']['fileset_name']

                new_output = output.get(task, {})
                new_errorcode = new_output.get('NotReported', {})
                for file_replica in row['doc']['files'].values():
                    for site in file_replica['locations']:
                        new_errorcode[site] = 0

                new_output['NotReported'] = new_errorcode
                output[task] = new_output

        for step in list(output):
            if True in [(steptype in step) for steptype in ['LogCollect', 'Cleanup']]:
                output.pop(step)

        return output


    def sum_errors(self):
        """
        :returns: The total number of errors reported by this workflow
        :rtype: int
        """

        errors = self.get_errors(True)
        return sum([num for codes in errors.values() for sites in codes.values()
                    for num in sites.values()])


    @cached_json('recovery_info')
    def get_recovery_info(self):
        """
        Get the recovery info for this workflow.

        :returns: a dictionary containing the information used in recovery.
                  The keys in this dictionary are arranged like the following::

                  { task: { 'sites_to_run': list(sites), 'missing_to_run': int() } }

        :rtype: dict
        """

        recovery_info = {}

        docs = get_json(self.url,
                        '/couchdb/acdcserver/_design/ACDC/_view/byCollectionName',
                        params={'key': '"%s"' % self.workflow,
                                'include_docs': 'true',
                                'reduce': 'false'},
                        use_cert=True)

        recovery_docs = [row['doc'] for row in docs.get('rows', [])]
        site_white_list = set(self.get_workflow_parameters()['SiteWhitelist'])

        for doc in recovery_docs:
            task = doc['fileset_name']
            # For each task, we have the following keys:
            # sites - a set of sites that the recovery docs say to run on.
            for replica, info in doc['files'].iteritems():
                # For fake files, just return the site whitelist
                if replica.startswith('MCFakeFile'):
                    locations = site_white_list
                else:
                    locations = set(info['locations'])

                vals = recovery_info.get(task, {})
                if not vals:
                    recovery_info[task] = {}

                recovery_info[task]['sites_to_run'] = \
                    list(set(vals.get('sites_to_run', set())) | locations)
                recovery_info[task]['missing_to_run'] = \
                    (vals.get('missing_to_run', 0) + info['events'])

        return recovery_info


    def site_to_run(self, task):
        """
        Gets a list of sites that a task in the workflow can run at

        :param str task: The full name of the task to find sites for
        :returns: a list of site to run at
        :rtype: list
        """

        site_set = self.get_recovery_info().get(task, {}).get('sites_to_run', [])
        out_list = []
        all_site_list = site_list()

        for site in site_set:
            clean_site = re.sub(r'_(ECHO_)?(Disk|MSS)$', '', site)
            if clean_site not in out_list and clean_site and \
                    clean_site in all_site_list:
                out_list.append(clean_site)

        out_list.sort()

        return out_list

    @cached_json('jobdetail')
    def _get_jobdetail(self):
        """
        Get the jobdetail from the wmstatsserver

        :returns: The job detail json from the server or cache
        :rtype: dict
        """

        return get_json(self.url,
                        '/wmstatsserver/data/jobdetail/%s' % self.workflow,
                        use_cert=True)

    def get_explanation(self, errorcode, step=''):
        """
        Gets a list of error logs for a given error code.

        :param str errorcode: The error code to explain
        :param str step: The full name of the step to return explanations from
        :returns: list of error logs
        :rtype: list
        """

        if self.explanations is None:
            self.explanations = defaultdict(lambda: defaultdict(lambda: []))
            result = self._get_jobdetail()
            for stepname, stepdata in result['result'][0].get(self.workflow, {}).iteritems():
                # Get the errors from both 'jobfailed' and 'submitfailed' details
                for error, site in [(error, site) for status in ['jobfailed', 'submitfailed'] \
                                        for error, site in stepdata.get(status, {}).items()]:
                    if error == '0':
                        continue

                    for sitename, samples in site.iteritems():
                        for detail in [values for sample in samples['samples']
                                       for errs in sample['errors'].values()
                                       for values in errs]:

                            self.explanations[error][stepname].append('\n\n'.join(
                                ['Site name: %s' % sitename,
                                 '%s (Exit code: %s)' % (detail['type'], detail['exitCode']),
                                 detail['details']]))

        explain = self.explanations.get(errorcode, {'': ['No info for this error code']})

        if step in explain.keys():
            return explain[step]

        return [val for expl in explain.values() for val in expl]

    def get_prep_id(self):
        """
        :returns: the PrepID for this workflow
        :rtype: str
        """

        return str(self.get_workflow_parameters().get('PrepID', 'NoPrepID'))


class PrepIDInfo(Info):
    """
    A class that just holds a small amount of information about a given PrepID.
    """

    def __init__(self, prep_id, url='cmsweb.cern.ch'):
        super(PrepIDInfo, self).__init__()
        self.prep_id = prep_id
        self.url = url

    def __str__(self):
        return 'prepIDinfo_%s' % self.prep_id

    @cached_json('requests')
    def get_requests(self):
        """
        :returns: The requests for the Prep ID from ReqMgr2 API
        :rtype: dict
        """
        if self.prep_id == 'NoPrepID':
            return None

        result = get_json(self.url, '/reqmgr2/data/request',
                          params={'prep_id': self.prep_id, 'detail': 'true'},
                          use_cert=True)

        if not result['result']:
            return None

        return result['result'][0]

    def get_workflows_requesttime(self):
        """
        :returns: A list of tuples containing (workflow name, timestamp of request)
        :rtype: list
        """
        request = self.get_requests()

        return [(workflow, time.mktime(datetime.datetime(*value['RequestDate']).timetuple())) \
                    for workflow, value in request.iteritems()]

    def get_workflows(self):
        """
        :returns: A list of tuples containing (workflow name, timestamp of request)
        :rtype: list
        """

        return [
            workflow for workflow, _ in
            self.get_workflows_requesttime()
        ]
