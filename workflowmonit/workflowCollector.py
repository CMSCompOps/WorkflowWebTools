#!/usr/bin/env python
from __future__ import print_function

import os
import re
import sys
import json
import time
import gzip
import shutil
import threading
from collections import defaultdict

import yaml
import cx_Oracle
from workflowwebtools import workflowinfo
from workflowwebtools import errorutils


def save_json(json_obj, filename='tmp', gzipped=False):
    """
    save json object to a local formatted text file, for debug

    :param dict json_obj: the json object
    :param str filename: the base name of the file to be saved
    :param bool gzipped: if gzip output document, default is False
    :returns: full filename

    :rtype: str
    """

    fn = "{}.json".format(filename)
    msg = json.dumps(json_obj, sort_keys=True, indent=4, separators=(',', ': '))

    if gzipped:
        fn += '.gz'
        with gzip.open(fn, 'wb') as f:
            f.write(msg.encode())
    else:
        with open(fn, 'w') as f:
            f.write(msg)

    return fn


def get_yamlconfig(configPath):
    '''
    get a dict of config file (YAML) pointed by configPath.

    :param str configPath: path of config file
    :returns: dict of config

    :rtype: dict
    '''

    if not os.path.isfile(configPath):
        return {}

    try:
        return yaml.load(open(configPath).read(), Loader=yaml.FullLoader)
    except:
        return {}


def invalidate_caches(cacheDir=None):
    '''
    remove json caches pointed by cacheDir

    :param str cache_dir: path of caching directory
    :returns: None
    '''

    cache_dir = cacheDir or os.path.join(
        os.environ.get('TMPDIR', '/tmp'), 'workflowinfo')

    try:
        shutil.rmtree(cache_dir)
    except:
        print('Fail to remove caches: ', cache_dir)
        pass

    try:
        os.mkdir(cache_dir)
    except:
        pass


def get_workflowlist_from_db(config, queryCmd):
    '''
    get a list of workflows from oracle db from a config dictionary which has a ``oracle`` key.

    :param dict config: config dictionary
    :param str queryCmd: SQL query command
    :returns: list of workflow names that are LIKE running

    :rtype: list
    '''

    if 'oracle' not in config:
        return []

    oracle_db_conn = cx_Oracle.connect(
        *config['oracle'])  # pylint:disable=c-extension-no-member
    oracle_cursor = oracle_db_conn.cursor()
    oracle_cursor.execute(queryCmd)
    wkfs = [row for row, in oracle_cursor]
    oracle_db_conn.close()

    return wkfs


def get_workflow_from_db(configPath, queryCmd):
    '''
    get a list of :py:class:`WorkflowInfo` objects by parsing the oracle db
    indicated in ``config.yml`` pointed by configpath.

    :param str configPath: path of config file
    :param str queryCmd: SQL query command
    :returns: list of :py:class:`WorkflowInfo`

    :rtype: list
    '''

    wf_list = []

    config = get_yamlconfig(configPath)
    if not config:
        return wf_list

    wfs = get_workflowlist_from_db(config, queryCmd)
    if wfs:
        wf_list = [workflowinfo.WorkflowInfo(wf) for wf in wfs]

    return wf_list


def cleanup_shortlog(desc):
    """
    clean up given string by:

    1. remove any HTML tag ``<>``
    2. remove square brackets label ``[]``
    3. remove char ``\\``
    4. replace successive whitespace with a single one
    5. remove single quote/double quote

    :param str desc: a description string
    :returns: a cleaned description string

    :rtype: str
    """

    cleaned = re.compile(r'<.*?>').sub('', desc)
    cleaned = re.compile(r'\[.*?\]').sub('', cleaned)
    cleaned = cleaned.replace('\\', '')
    cleaned = re.compile('\s+').sub(' ', cleaned)
    cleaned = cleaned.replace('"', "'").replace("'", '')

    return cleaned


def short_errorlog(log,
                   buzzwords=['error', 'fail',
                              'exception', 'maxrss', 'timeout'],
                   ignorewords=['start', 'begin', 'end', 'above', 'below']):
    r"""
    pruned the lengthy error logs extracted from wmstats to a short message,
    with a logic of combination of ``buzzwords`` and ``ignorewords``.

    - First if ``log`` is short enouggh that does not contain a ``\n``, return it.
    - Else split the log with common delimiters to list, then clean up each entry with :py:func:`cleanup_shortlog`,
        - from begining, if a entry does not contain any word in ``ignorewords`` list, it shall need attention;
        - if a entry contains any word in buzzwords, it shall be buzzed;
        - if a buzzed entry contains less than 3 words, it shall be skipped.( not informative enough)

    - if anything in buzzed list, return a string concatenating all buzzed entries;
    - else if anything in attentioned list, return the first entry;
    - else returns the first entry after clean up only.

    :param str log: length log string from wmstats
    :param list buzzwords: list of words that shall draw attention
    :param list ignorewords: list of words that shall be ignored at any conditions
    :returns: shorted log that shall reflect key information

    :rtype: str
    """

    log = log.strip()
    if '\n' not in log:
        return log

    piecesList = re.split('; |, |:|\*|\n+', log)
    piecesList = [cleanup_shortlog(x) for x in piecesList]

    attentionedPieces = list()
    buzzedPieces = list()

    for piece in piecesList:
        piece = piece.strip()
        raw = piece.lower()

        if any(kw in raw for kw in ignorewords):
            continue
        attentionedPieces.append(piece)

        if any(kw in raw for kw in buzzwords):
            buzzedPieces.append(piece)

    if buzzedPieces:
        buzzedPieces = [x for x in set(buzzedPieces) if len(
            x.split(' ')) > 2]  # too short to be informative
    if buzzedPieces:
        return '; '.join(buzzedPieces)

    # should save exceptional error logs to enrich buzzwords
    if attentionedPieces:
        return attentionedPieces[0]
    else:
        return piecesList[0]


def extract_keywords(description,
                     buzzwords=['error', 'errors', 'errormsg', 'fail',
                                'failed', 'failure', 'kill', 'killed', 'exception'],
                     blacklistwords=['start', 'begin',
                                     'end', 'above', 'below'],
                     whitelistwords=['timeout', 'maxrss', 'nojobreport']):
    """
    extract keywords from shortened error log,
    with a logic of combination of ``buzzwords``, ``blacklistwords`` and ``whitelistwords``.

    For each word in the ``description``, if it's in ``whitelistwords``, add to return;
    if any word in ``buzzwords`` is a subset of this word, add to return.
    In the end, if any word in ``blacklistwords`` shows up in the to-return list, removes it.

    :param str description: shortened error log
    :param list buzzwords: list of words that shall draw attention
    :param list blacklistwords: list of words that should not be treated as keyword
    :param list whitelistwords: list of words that will always be treated as keyword
    :returns: a set of keywords

    :rtype: set
    """

    kwset = set()

    for word in re.compile('\w+').findall(description):
        word = word.strip()
        raw = word.lower()

        if any(kw in raw for kw in whitelistwords):
            kwset.add(word)

        for kw in buzzwords:
            if kw in raw and (raw not in buzzwords):
                kwset.add(word)

    for kw in blacklistwords:
        kwset.discard(kw)

    return kwset


def error_logs(workflow):
    """
    Given a :py:class:`WorkflowInfo`, builds up a structured entity
    representing all available necessary error information via WorkflowInfo's property.::

        {'taskName' :
            {'errorCode' :
                {'siteName' :

                    [
                        {
                            'secondaryErrorCodes' : [],
                            'errorKeywords' : [],
                            'errorChain' : [(typecode, shortLog), ...]
                        },

                        ...
                    ]
                }
            }
        }

    :param workflow: A :py:class:`WorkflowInfo` object
    :returns: error info parsed from logs

    :rtype: collections.defaultdict
    """

    error_logs = defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: []
            )
        )
    )

    wf_jobdetail = workflow._get_jobdetail()
    wf_stepinfo = wf_jobdetail['result'][0].get(workflow.workflow, {})

    if not wf_stepinfo:
        return error_logs

    for stepname, stepdata in wf_stepinfo.items():
        _taskName = stepname.split('/')[-1]
        # Get the errors from both 'jobfailed' and 'submitfailed' details
        for error, sitedata in [
            (error, sitedata) for status in ['jobfailed', 'submitfailed']
            for error, sitedata in stepdata.get(status, {}).items()
        ]:
            if error == '0':
                continue
            _errorcode = int(error)

            for _sitename, siteinfo in sitedata.items():
                _errorsamples = list()

                for sample in siteinfo['samples']:
                    _timestamp = sample['timestamp']
                    errorcells = [e for cateInfo in sample['errors'].values()
                                  for e in cateInfo]
                    errorcells_unique = list()
                    for ec in errorcells:
                        if ec in errorcells_unique:
                            continue
                        errorcells_unique.append(ec)

                    _secondaryCodes = list()
                    _errorKeywords = list()
                    _errorChainAsDicts = list()

                    for ec in errorcells_unique:

                        type_ = ec['type']
                        code_ = ec['exitCode']
                        shortdetail_ = short_errorlog(ec['details'])

                        if code_ != _errorcode:
                            _secondaryCodes.append(code_)

                        _errorKeywords.extend(list(
                            extract_keywords(' '.join([
                                type_,
                                shortdetail_
                            ]))
                        ))

                        _errorChainAsDicts.append({
                            "errorType": type_,
                            "exitCode": code_,
                            "description": shortdetail_
                        })

                    _errorsamples.append({
                        'secondaryErrorCodes': list(set(_secondaryCodes)),
                        'errorKeywords': list(set(_errorKeywords)),
                        'errorChain': _errorChainAsDicts,
                        'timeStamp': _timestamp
                    })

                error_logs[_taskName][_errorcode][_sitename] = _errorsamples

    return error_logs


def error_summary(workflow):
    """
    Given a :py:class:`WorkflowInfo`,  build a minimal error summary via :py:func:`workflow.get_errors` method.::

        {'taskName':
            {'errors': [
                {
                    'errorCode' : errorCode,
                    'siteName' : siteName,
                    'counts' : counts
                },

                 ...

                ],
            'siteNotReported': []
            }
        }

    :param workflow: A :py:class:`WorkflowInfo` object
    :returns: A dict representing mimnial error summary

    :rtype: dict
    """

    error_summary = dict()

    errorInfo = workflow.get_errors(get_unreported=True)
    if not errorInfo:
        return error_summary

    for fullTaskName, taskErrors in errorInfo.items():
        taskName = fullTaskName.split('/')[-1]
        if not taskName:
            continue

        errorList = list()
        noReportSite = list(taskErrors.get('NotReported', {}).keys())
        for errorCode, siteCnt in taskErrors.items():
            if errorCode == 'NotReported':
                continue

            for siteName, counts in siteCnt.items():
                errorList.append({
                    'errorCode': int(errorCode),
                    'siteName': siteName,
                    'counts': counts
                })

        error_summary[taskName] = {
            'errors': errorList,
            'siteNotReported': noReportSite
        }

    return error_summary


def populate_error_for_workflow(workflow):
    """
    Given a :py:class:`WorkflowInfo`,  build an ultimate error summary with
    :py:func:`error_logs`, :py:func:`error_summary` method and wmstats API.

    :param workflow: A :py:class:`WorkflowInfo` object
    :returns: A dict representing all available error info

    :rtype: dict
    """

    if isinstance(workflow, str):
        workflow = workflowinfo.WorkflowInfo(workflow)
    assert(isinstance(workflow, workflowinfo.WorkflowInfo))

    workflow_summary = {
        "name": workflow.workflow,
        "status": None,
        "type": None,
        "failureRate": 0.,
        "totalError": 0,
        "failureKeywords": [],
        "transitions": [],
        "tasks": {}
    }

    workflow_summary['failureRate'] = workflow.get_failure_rate()
    wf_reqdetail = workflow._get_reqdetail()
    #save_json(wf_reqdetail, 'wf_reqdetail')

    wfData = wf_reqdetail.get(workflow.workflow, {})
    if not wfData:
        return workflow_summary

    # info extracted from wmstats request API
    agentJobInfo = wfData.get('AgentJobInfo', {})
    requestStatus = wfData.get('RequestStatus', None)
    requestType = wfData.get('RequestType', None)
    if not all([agentJobInfo, requestStatus, requestType]):
        return workflow_summary

    requestTransition = wfData.get('RequestTransition', [])

    workflow_summary['status'] = requestStatus
    workflow_summary['type'] = requestType
    workflow_summary['transitions'] = requestTransition

    nfailure = 0
    for agent, agentdata in agentJobInfo.items():
        status = agentdata.get('status', {})
        tasks = agentdata.get('tasks', {})
        if not all([status, tasks]):
            continue

        for ftype, num in status.get('failure', {}).items():
            nfailure += num

        for taskFullName, taskData in tasks.items():
            taskName = taskFullName.split('/')[-1]

            inputTask = None
            if len(taskFullName.split('/')) > 3:
                inputTask = taskFullName.split('/')[-2]

            jobType = taskData.get('jobtype', None)
            taskStatus = taskData.get('status', {})

            taskSiteError = dict()

            if taskStatus and taskStatus.get('failure', {}):
                for site, siteData in taskData.get('sites', {}).items():
                    errCnt = 0
                    errCnts = siteData.get('failure', {})
                    if not errCnts:
                        continue

                    for ftype, cnt in errCnts.items():
                        errCnt += cnt

                    taskSiteError[site] = errCnt

            _task = workflow_summary['tasks'].get(taskName, None)
            if _task:
                if 'jobType' not in _task.keys():
                    _task["jobType"] = jobType
                if 'inputTask' not in _task.keys():
                    _task['inputTask'] = inputTask
                if 'siteErrors' not in _task.keys():
                    _task["siteErrors"] = taskSiteError
                else:
                    for site, errors in taskSiteError.items():
                        if site in _task["siteErrors"].keys():
                            _task["siteErrors"][site] += errors
                        else:
                            _task["siteErrors"][site] = errors

                workflow_summary['tasks'][taskName] = _task
            else:
                workflow_summary['tasks'][taskName] = {
                    "inputTask": inputTask,
                    "jobType": jobType,
                    "siteErrors": taskSiteError,
                    "errors": [],
                    "siteNotReported": []
                }

    # remove tasks that does not have any error
    taskToDel = list()
    for taskname, taskinfo in workflow_summary['tasks'].items():
        if 'siteErrors' in taskinfo and (not taskinfo['siteErrors']):
            taskToDel.append(taskname)
    for taskname in taskToDel:
        workflow_summary['tasks'].pop(taskname, None)

    workflow_summary['totalError'] = nfailure

    if workflow_summary['status'] != 'rejected':

        wf_errorSummary = error_summary(workflow)
        wf_errorLog = error_logs(workflow)

        # add information from errorSummary
        for taskName, taskErrors in wf_errorSummary.items():
            if taskName in workflow_summary['tasks'].keys():
                workflow_summary['tasks'][taskName].update(taskErrors)

        # add information from errorLog
        for taskName, taskErrorLogInfo in wf_errorLog.items():

            if taskName not in workflow_summary['tasks'].keys():
                continue
            for errorCode, siteInfo in taskErrorLogInfo.items():
                for site, info in siteInfo.items():

                    for e in workflow_summary['tasks'][taskName].get('errors', []):
                        if e.get('siteName', None) != site:
                            continue
                        if e.get('errorCode', None) != errorCode:
                            continue

                        if len(info):
                            e.update(info[0])

        # fill failureKeywords list
        allKeywords = [kw
                       for task in workflow_summary['tasks'].values()
                       for error in task.get('errors', [])
                       for kw in error.get('errorKeywords', [])
                       ]
        workflow_summary['failureKeywords'] = list(set(allKeywords))

    # last step, nest in task key(TaskName) as a key-value pair
    tasksAsList = []
    for taskname, taskinfo in workflow_summary['tasks'].items():
        taskinfo.update({"name": taskname})
        taskinfo['siteErrors'] = [
            {
                "site": site,
                "counts": counts
            } for site, counts in taskinfo['siteErrors'].items()
        ]  # convert 'siteErrors' from a dict to a list of dict
        tasksAsList.append(taskinfo)
    workflow_summary['tasks'] = tasksAsList

    return workflow_summary


def _get_acdc_response(wfstr):
    """
    debug
    """

    from cmstoolbox.webtools import get_json
    response = get_json(
        'cmsweb.cern.ch',
        '/couchdb/acdcserver/_design/ACDC/_view/byCollectionName',
        {'key': '"{0}"'.format(
                wfstr), 'include_docs': 'true', 'reduce': 'false'},
        use_cert=True
    )
    return response


def filter_n_collector(res, q, minFailureRate=0.2):

    while not q.empty():
        wf = q.get()
        try:
            if wf.get_failure_rate() > minFailureRate:
                res.append(populate_error_for_workflow(wf))
        except:
            pass
        q.task_done()
    return True


def main():

    start_time = time.time()

    # status_location = '/home/wsi/workdir/statuses.json' # dummy
    CONFIG_FILE_PATH = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'config.yml')
    #DB_QUERY_CMD = "SELECT NAME FROM CMS_UNIFIED_ADMIN.WORKFLOW WHERE WM_STATUS LIKE 'running%'"
    DB_QUERY_CMD = "SELECT NAME FROM CMS_UNIFIED_ADMIN.workflow WHERE lower(STATUS) LIKE '%manual%'"
    wfs = get_workflow_from_db(CONFIG_FILE_PATH, DB_QUERY_CMD)

    print("Number of workflows retrieved from Oracle DB: ", len(wfs))
    invalidate_caches()

    try:
        from Queue import Queue
    except ImportError:
        from queue import Queue # pylint: disable=import-error
    q = Queue()
    num_threads = min(150, len(wfs))

    for wf in wfs:
        q.put(wf)
    results = list()
    for _ in range(num_threads):
        t = threading.Thread(target=filter_n_collector, args=(results, q, ))
        t.daemon = True  # seting threads as "daemon" allows main program to exit
        # eventually even if these dont finish correctly.
        t.start()
    q.join()
    print("Number of workflows that has >20% failure rate: ", len(results))

    elasped_time = time.time() - start_time
    print('Takes {0} s in total.'.format(elasped_time))

    ###################################

    # key, ws = wfs[1]
    # print(key)
    # pprint(populate_error_for_workflow(ws))
    # pprint(error_summary(ws))
    # pprint(error_logs(ws))
    # save_json(error_logs(ws), 'wf_errorlog')
    # save_json(populate_error_for_workflow(ws), 'wf_document')
    save_json(results, 'wfc_results')


if __name__ == '__main__':
    main()
