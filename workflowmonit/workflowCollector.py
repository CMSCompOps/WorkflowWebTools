#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import json
import yaml
import re
import shutil
import cx_Oracle
from collections import defaultdict, OrderedDict
from pprint import pprint
import time


from workflowwebtools import workflowinfo
from workflowwebtools import errorutils


def save_json(json_obj, filename='tmp'):
    """
    save json object to a local formatted text file, for debug

    :param dict json_obj: the json object
    :param str filename: the base name of the file to be saved
    :returns: None
    """

    with open('%s.json' % filename, 'w') as tmp:
        tmp.write(json.dumps(json_obj, sort_keys=True, indent=4, separators=(',', ': ')))


def get_yamlconfig(configPath):
    '''
    get a dict of config file (YAML) pointed by configPath.

    :param str configPath: path of config file
    :returns: dict of config

    :rtype: dict
    '''

    if not os.path.isfile(configPath): return {}

    try:
        return yaml.load(open(configPath).read())
    except:
        return {}


def invalidate_caches(cacheDir=None):
    '''
    remove json caches pointed by cacheDir

    :param str cache_dir: path of caching directory
    :returns: None
    '''

    cache_dir = cacheDir or os.path.join(os.environ.get('TMPDIR', '/tmp'), 'workflowinfo')
    
    try:
        shutil.rmtree(cache_dir)
    except:
        print('Fail to remove caches: ', cache_dir)
        pass


def get_workflow_from_status(path):
    '''
    get a dict of :py:class:`WorkflowInfo` objects by parseing the statuses.json file given the path.
    {'workflow' : WorkflowInfo}

    :param str path: path of statuses.json
    :returns: dict of :py:class:`WorkflowInfo`s with its string as key

    :rtype: dict
    '''

    wf_dict = {}

    wfs = errorutils.get_workflow_list_from_location(path)
    if wfs:
        wf_dict = {wf : workflowinfo.WorkflowInfo(wf) for wf in wfs}

    return wf_dict


def get_workflowlist_from_db(config, queryCmd):
    '''
    get a list of workflows from oracle db from a config dictionary which has a 'oracle' key.

    :param dict config: config dictionary
    :param str queryCmd: SQL query command
    :returns: list of workflow names that are LIKE running

    :rtype: list
    '''

    if 'oracle' not in config: return []

    oracle_db_conn = cx_Oracle.connect(*config['oracle']) # pylint:disable=c-extension-no-member
    oracle_cursor = oracle_db_conn.cursor()
    oracle_cursor.execute(queryCmd)
    wkfs = [row for row, in oracle_cursor]
    oracle_db_conn.close()
    
    return wkfs


def get_workflow_from_db(configPath, queryCmd):
    '''
    get a dict of :py:class:`WorkflowInfo` objects by parseing the oracle db indicated in config.yml
    pointed by configpath.
    {'workflow' : WorkflowInfo}

    :param str configPath: path of config file
    :param str queryCmd: SQL query command
    :returns: dict of :py:class:`WorkflowInfo`s with its string as key

    :rtype: dict
    '''

    wf_dict = {}

    config = get_yamlconfig(configPath)
    if not config: return wf_dict

    wfs = get_workflowlist_from_db(config, queryCmd)
    if wfs:
        wf_dict = {wf : workflowinfo.WorkflowInfo(wf) for wf in wfs}

    return wf_dict


def cleanup_shortlog(desc):
    """
    clean up given string by:
    1. remove any HTML tag <>
    2. remove square brackets label []
    3. reemove char '\'
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
                   buzzwords=['error', 'fail', 'exception', 'maxrss', 'timeout'],
                   ignorewords = ['start', 'begin', 'end', 'above', 'below']):
    """
    pruned the lengthy error logs extracted from wmstats to a short message,
    with a logic of combination of `buzzwords` and `ignorewords`.
    
    First if `log` is short enouggh that does not contain a \n, return it.
    Else split the log with common delimiters to list,
    then clean up each entry with :py:func:`cleanup_shortlog`,
    from begining, if a entry does not contain any word in `ignorewords` list, it shall need attention;
    if a entry contains any word in buzzwords, it shall be buzzed;
    if a buzzed entry contains less than 3 words, it shall be skipped.( not informative enough)

    if anything in buzzed list, return a string concatenating all buzzed entries;
    else if anything in attentioned list, return the first entry;
    else returns the first entry after clean up only.

    :param str log: length log string from wmstats
    :param list buzzwords: list of words that shall draw attention
    :param list ignorewords: list of words that shall be ignored at any conditions
    :returns: shorted log that shall reflect key information
    
    :rtype: str
    """

    log = log.strip()
    if '\n' not in log: return log

    piecesList = re.split('; |, |:|\*|\n+', log)
    piecesList = [cleanup_shortlog(x) for x in piecesList]

    attentionedPieces = list()
    buzzedPieces      = list()

    for piece in piecesList:
        piece = piece.strip()
        raw = piece.lower()

        if any(kw in raw for kw in ignorewords): continue
        attentionedPieces.append( piece )

        if any(kw in raw for kw in buzzwords):
            buzzedPieces.append( piece )

    if buzzedPieces:
        buzzedPieces = [x for x in set(buzzedPieces) if len(x.split(' '))>2] # too short to be informative
    if buzzedPieces:
        return '; '.join(buzzedPieces)

    # should save exceptional error logs to enrich buzzwords
    if attentionedPieces:
        return attentionedPieces[0]
    else:
        return piecesList[0]

def extract_keywords(description,
                     buzzwords = ['error', 'errors', 'errormsg', 'fail', 'failed', 'failure', 'kill', 'killed', 'exception'],
                     blacklistwords = ['start', 'begin', 'end', 'above', 'below'],
                     whitelistwords = ['timeout', 'maxrss', 'nojobreport']):
    """
    extract keywords from shortened error log,
    with a logic of combination of `buzzwords`, `blacklistwords` and `whitelistwords`.

    For each word in the `description`, if it's in `whitelistwords`, add to return;
    if any word in `buzzwords` is a subset of this word, add to return.
    In the end, if any word in `blacklistwords` shows up in the to-return list, removes it.

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
    representing all available necessary error information via WorkflowInfo's property.

        {taskName : {errorCode : {siteName : {'secondaryErrorCodes' : [], 'errorKeywords' : [], 'errorChain' : [(typecode, shortLog), ...] } } } }

    :param :py:class:`WorkflowInfo` workflow: A :py:class:`WorkflowInfo` object
    :returns: error info parsed from logs

    :rtype: collection.defaultdict
    """

    error_logs = defaultdict(lambda: defaultdict(lambda: []))

    # dummpy call to get explaination filled
    workflow.get_explanation(0)
    explanations = workflow.explanations
    if not explanations: return error_logs

    keys = [(error, taskFullName) for error in explanations.keys() \
                                  for taskFullName in explanations[error].keys()]

    for error, taskFullName in keys:
        taskName = taskFullName.split('/')[-1]
        content = list()
        for errorItem in explanations[error][taskFullName]:
            _siteName, x = errorItem.split('\n\n', 1)
            _typeCode, _log = x.split('\n\n', 1)

            content.append({
                'site': _siteName.split(' ')[-1],
                'type': _typeCode,
                'info': short_errorlog(_log)})

        sitePivoted = defaultdict(list)
        for entry in content:
            sitePivoted[entry['site']].append((entry['type'], entry['info']))

        compactInfo = dict()
        for site, info in sitePivoted.iteritems():
            errorChain = OrderedDict.fromkeys(info) # remove duplicates,but also would like to preserve
                                                    # order, set() does not.

            secondaryErrorCodes = list()
            errorKeywords       = set()
            errorChainAsDicts   = list()
            for typeCode, shortDescrip in errorChain.keys():
                # typeCode string example: 'NoJobReport (Exit code: 99303)'
                parenthesesGroup = re.compile(r'\((.+)\)').search(typeCode).group()
                _code  = int( parenthesesGroup[1:-1].split(':')[-1] )
                _type = typeCode.replace(parenthesesGroup, '').strip()
                if _code != int(error):
                    secondaryErrorCodes.append( _code )
                errorKeywords.update(extract_keywords(' '.join([typeCode, shortDescrip])))
                errorChainAsDicts.append({
                    "errorType"   : _type,
                    "exitCode"    : _code,
                    "description" : shortDescrip
                    })

            compactInfo[site] = {
                    'secondaryErrorCodes' : secondaryErrorCodes,
                    'errorKeywords'       : list(errorKeywords),
                    'errorChain'          : errorChainAsDicts
                    }
        
        error_logs[taskName][error] = compactInfo

    return error_logs


def error_summary(workflow):
    """
    Given a :py:class:`WorkflowInfo`,  build a minimal error summary via `workflow.get_errors` method.

        {taskName : {'errors': [{'errorCode' : errorCode, 'siteName' : siteName, 'counts' : counts}, ...],
                     'siteNotReported': []}

    :param :py:class:`WorkflowInfo` workflow: A :py:class:`WorkflowInfo` object
    :returns: A dict representing mimnial error summary

    :rtype: dict
    """

    error_summary = dict()

    errorInfo = workflow.get_errors(get_unreported=True)
    if not errorInfo: return error_summary

    for fullTaskName, taskErrors in errorInfo.iteritems():
        taskName = fullTaskName.split('/')[-1]
        if not taskName: continue

        errorList = list()
        noReportSite = list(taskErrors.get('NotReported', {}).keys())
        for errorCode, siteCnt in taskErrors.iteritems():
            if errorCode == 'NotReported': continue

            for siteName, counts in siteCnt.iteritems():
                errorList.append({
                    'errorCode' : errorCode,
                    'siteName'  : siteName,
                    'counts'    : counts
                    })
        
        error_summary[taskName] = {
                'errors': errorList,
                'siteNotReported': noReportSite
                }

    return error_summary


def populate_error_for_workflow(workflow):
    """
    Given a :py:class:`WorkflowInfo`,  build an ultimate error summary with
    :py:func:`error_logs`, :py:func:`error_summary` method and wmstats `request` API.

    :param :py:class:`WorkflowInfo` workflow: A :py:class:`WorkflowInfo` object
    :returns: A dict representing all available error info

    :rtype: dict
    """


    workflow_summary = {
            "name" : workflow.workflow,
            "status" : None,
            "failureRate": 0.,
            "totalError": 0,
            "failureKeywords": [],
            "tasks": {}
            }

    workflow_summary['failureRate'] = workflow.get_failure_rate()
    wf_reqdetail = workflow._get_reqdetail()
    #save_json(wf_reqdetail, 'wf_reqdetail')

    wfData = wf_reqdetail.get(workflow.workflow, {})
    if not wfData: return workflow_summary

    # info extracted from wmstats request API
    agentJobInfo   = wfData.get('AgentJobInfo', {})
    requestStatus  = wfData.get('RequestStatus', None)
    requestType    = wfData.get('RequestType', None)
    if not all([agentJobInfo, requestStatus, requestType]):
        return workflow_summary

    workflow_summary['status'] = requestStatus
    workflow_summary['type']   = requestType

    nfailure = 0
    for agent, agentdata in agentJobInfo.iteritems():
        status = agentdata.get('status', {})
        tasks  = agentdata.get('tasks', {})
        if not all([status, tasks]):
            continue

        for ftype, num in status.get('failure', {}).iteritems():
            nfailure += num
        
        for taskFullName, taskData in tasks.iteritems():
            taskName = taskFullName.split('/')[-1]

            inputTask = None
            if len(taskFullName.split('/')) > 3:
                inputTask = taskFullName.split('/')[-2]

            jobType  = taskData.get('jobtype', None)
            taskStatus = taskData.get('status', {})

            taskSiteError = dict()

            if taskStatus and taskStatus.get('failure', {}):
                for site, siteData in taskData.get('sites', {}).iteritems():
                    errCnt = 0
                    errCnts = siteData.get('failure', {})
                    if not errCnts: continue

                    for ftype, cnt in errCnts.iteritems():
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
                    for site, errors in taskSiteError.iteritems():
                        if site in _task["siteErrors"].keys():
                            _task["siteErrors"][site] += errors
                        else:
                            _task["siteErrors"][site] = errors

                workflow_summary['tasks'][taskName] = _task
            else:
                workflow_summary['tasks'][taskName] = {
                        "inputTask"       : inputTask,
                        "jobType"         : jobType,
                        "siteErrors"      : taskSiteError,
                        "errors"          : [],
                        "siteNotReported" : []
                        }
                
    # remove tasks that does not have any error
    taskToDel = list()
    for taskname, taskinfo in workflow_summary['tasks'].iteritems():
        if 'siteErrors' in taskinfo and (not taskinfo['siteErrors']):
            taskToDel.append(taskname)
    for taskname in taskToDel:
        workflow_summary['tasks'].pop(taskname, None)

    workflow_summary['totalError'] = nfailure


    if workflow_summary['status'] != 'rejected':

        wf_errorSummary = error_summary(workflow)
        wf_errorLog     = error_logs(workflow)

        # add information from errorSummary
        for taskName, taskErrors in wf_errorSummary.iteritems():
            if taskName in workflow_summary['tasks'].keys():
                workflow_summary['tasks'][taskName].update( taskErrors )

        # add information from errorLog
        for taskName, taskErrorLogInfo in wf_errorLog.iteritems():

            if taskName not in workflow_summary['tasks'].keys(): continue
            for errorCode, siteInfo in taskErrorLogInfo.iteritems():
                for site, info in siteInfo.iteritems():

                    for e in workflow_summary['tasks'][taskName].get('errors', []):
                        if e.get('siteName', None) != site: continue
                        if e.get('errorCode', None) != errorCode: continue

                        e.update(info)
                        e['errorCode'] = int(e['errorCode']) # errorCode as an integer

        # fill failureKeywords list
        allKeywords = [kw \
                for task in workflow_summary['tasks'].values()
                for error in task.get('errors', []) \
                for kw in error.get('errorKeywords', []) \
                ]
        workflow_summary['failureKeywords'] = list(set(allKeywords))

    # last step, nest in task key(TaskName) as a key-value pair
    tasksAsList = []
    for taskname, taskinfo in workflow_summary['tasks'].iteritems():
        taskinfo.update({"name": taskname})
        taskinfo['siteErrors'] = [
                {
                    "site"   : site,
                    "counts" : counts
                } for site, counts in taskinfo['siteErrors'].iteritems()
            ] # convert 'siteErrors' from a dict to a list of dict
        tasksAsList.append(taskinfo)
    workflow_summary['tasks'] = tasksAsList

    return workflow_summary

def get_acdc_response(wfstr):
    """
    debug
    """
    
    from cmstoolbox.webtools import get_json
    response = get_json(
            'cmsweb.cern.ch',
            '/couchdb/acdcserver/_design/ACDC/_view/byCollectionName',
            {'key':'"{0}"'.format(wfstr), 'include_docs': 'true', 'reduce': 'false'},
            use_cert=True
        )
    return response


def main():

    start_time = time.time()

    #status_location = '/home/wsi/workdir/statuses.json' # dummy
    CONFIG_PATH = '/home/wsi/workdir/config.yml'
    #DB_QUERY_CMD = "SELECT NAME FROM CMS_UNIFIED_ADMIN.WORKFLOW WHERE WM_STATUS LIKE 'running%'"
    DB_QUERY_CMD = "SELECT NAME FROM CMS_UNIFIED_ADMIN.workflow WHERE lower(STATUS) LIKE '%manual%'"
    wfs = get_workflow_from_db(CONFIG_PATH, DB_QUERY_CMD)

    #for i, wf in enumerate(wfs.keys()):
    #    print(i, wf)
    #    pprint( get_acdc_response(wf) )
    #'''

    #p = Pool(8)
    #result = p.map(populate_error_for_workflow, wfs.values())
    print("Number of workflows retrieved from Oracle DB: ", len(wfs))
    result = list()
    for i, wf in enumerate(wfs.values()):
        if wf.get_failure_rate() < 0.2: continue
        ws = populate_error_for_workflow(wf)
        print(i)
        result.append(ws)
        #pprint(ws)

    with open('result.json', 'w') as fp:
        json.dump(result, fp, indent=4)

    elasped_time = time.time() - start_time
    print('Takes {0} s'.format(elasped_time))
    #with open('toSaveExample.json', 'w') as outf:
    #    json.dump(
    #            populate_error_for_workflow(
    #                wfs.values()[2]
    #                ),
    #            outf,
    #            indent = 4
    #            )

    #'''
    #key, ws = wfs.items()[0]
    #print(key)
    #pprint(populate_error_for_workflow(ws))
    #pprint(error_summary(ws))
    #pprint(error_logs(ws))
    #save_json(error_logs(ws), 'wf_errorlog')
    

if __name__ == '__main__':
    main()
