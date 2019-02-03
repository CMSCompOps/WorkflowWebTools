#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import yaml
import socket
import time
import threading
import sqlite3
from Queue import Queue

from workflowwebtools import workflowinfo
from WMCore.Services.StompAMQ.StompAMQ import StompAMQ
from workflowmonit import workflowCollector as wc

CRED_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credential.yml')
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
LOGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')


def worker(res, q, completedWfs, minFailureRate=0.2, configPath=CONFIG_FILE_PATH):
    """
    Get item from queue, work on it, append result to `res`.

    :param list res: container to hold results
    :param list completedWfs: completed workflows, to avoid re-caching
    :param Queue q: queue
    :param float minFailureRate: minimum failure rate
    :param str configPath: path to config file
    """

    dbPath = wc.get_yamlconfig(configPath).get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workflow_status.sqlite')
    )
    DB_UPDATE_CMD = """INSERT OR REPLACE INTO workflowStatuses VALUES (?,?,?)"""

    while not q.empty():
        wf = q.get()
        if wf.workflow in completedWfs: continue
        try:
            failurerate = wf.get_failure_rate()
            if failurerate > minFailureRate:
                res.append(wc.populate_error_for_workflow(wf))

            toUpdate = (
                wf.workflow,
                wf._get_reqdetail().get(wf.workflow, {}).get('RequestStatus', ''),
                failurerate
                )
            if not all(toUpdate[:-1]): continue
            conn = sqlite3.connect(dbPath)
            with conn:
                c = conn.cursor()
                c.execute(DB_UPDATE_CMD, toUpdate)

        except:
            pass
        q.task_done()
    return True



def getCompletedWorkflowsFromDb(configPath):
    """
    Get completed workflow list from local status db

    :param str configPath: location of config file
    :returns: list of workflow (str)
    :rtype: list
    """

    config = wc.get_yamlconfig(configPath)
    if not config:
        sys.exit('Config file: {} not exist, exiting..'.format(configPath))
    dbPath = config.get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workflow_status.sqlite')
        )

    DB_CREATE_CMD = """CREATE TABLE IF NOT EXISTS workflowStatuses (
        name TEXT PRIMARY KEY,
        status TEXT,
        failurerate REAL
    );"""
    DB_QUERY_CMD = """SELECT * FROM workflowStatuses WHERE status IN ('running-closed', 'completed', 'aborted-archived', 'rejected-archived')"""

    res = []
    conn = sqlite3.connect(dbPath)
    with conn:
        c = conn.cursor()
        c.execute(DB_CREATE_CMD)
        for row in c.execute(DB_QUERY_CMD):
            res.append(row[0])

    return res


def updateWorkflowStatusToDb(configPath, wcErrorInfos):
    """
    update workflow status to local status db, with the information from wcErrorInfo

    :param str configPath: location of config file
    :param list wcErrorInfos: list of dicts returned by :py:func:`wc.filter_n_collect`
    :returns: True
    """

    config = wc.get_yamlconfig(configPath)
    if not config:
        sys.exit('Config path: {} not exist, exiting..'.format(configPath))
    dbPath = config.get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workflow_status.sqlite')
        )

    DB_CREATE_CMD = """CREATE TABLE IF NOT EXISTS workflowStatuses (
        name TEXT PRIMARY KEY,
        status TEXT,
        failurerate REAL
    );"""
    DB_UPDATE_CMD = """INSERT OR REPLACE INTO workflowStatuses VALUES (?,?,?)"""

    toUpdate = []
    for e in wcErrorInfos:
        entry = (
            e.get('name', ''),
            e.get('status', ''),
            e.get('failureRate', 0.)
        )
        if not all(entry[:-1]): continue
        toUpdate.append(entry)

    conn = sqlite3.connect(dbPath)
    with conn:
        c = conn.cursor()
        c.executemany(DB_UPDATE_CMD, toUpdate)

    return True


def buildDoc(configpath):
    """
    Given a path to the config file which contains oracle db connection info,
    returns a list of documents (each for one workflow)

    :param str configpath: location of config file
    :returns: list of documents

    :rtype: list
    """

    DB_QUERY_CMD = "SELECT NAME FROM CMS_UNIFIED_ADMIN.WORKFLOW WHERE WM_STATUS LIKE 'running%'"

    _wkfs = wc.get_workflow_from_db(configpath, DB_QUERY_CMD)
    completedWfs = getCompletedWorkflowsFromDb(configpath)
    wkfs = [w for w in _wkfs if w.workflow not in completedWfs]
    print('Number of workflows to query: ', len(wkfs))
    wc.invalidate_caches('/tmp/wsi/workflowinfo')

    q = Queue()
    num_threads = min(150, len(wkfs))
    for wf in wkfs: q.put(wf)

    results = list()
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(results, q, completedWfs, ))
        t.daemon = True
        t.start()
    q.join()

    updateWorkflowStatusToDb(configpath, results)
    print('Number of updated workflows: ', len(results))

    return results


def sendDoc(cred, doc):
    """
    Given a credential dict and documents to send, make notification.

    :param dict cred: credential required by StompAMQ
    :param list doc: documents to send
    :returns: None
    """


    amq = StompAMQ(
            None, # username
            None, # password
            cred['producer'],
            cred['topic'],
            host_and_ports = None, # default [('agileinf-mb.cern.ch', 61213)]
            cert = cred['cert'],
            key = cred['key']
            )


    docType = 'dict'
    docId = '{0}:{1}:{2}'.format(cred['producer'], socket.gethostname(), int(time.time()))
    results = amq.send(
            amq.make_notification(doc, docType, docId)
            )
    print('### results from AMQ %s' % len(results))


def dummy(doc):
    """
    Debug
    """

    amq = StompAMQ(
            'wsi',
            '123456',
            'toolsandint-workflows-collector',
            'cms.toolsandint.workflowsinfo',
            [('vocms0116.cern.ch', 8080)]
            )

    docType = 'dict'
    docId = 'toolsandint-workflows-collector:vocms0116.cern.ch:{0}'.format(int(time.time()))
    toSend = amq.make_notification(doc, docType, docId)

    return toSend



if __name__ == "__main__":

    print('\n', time.asctime())

    cred = wc.get_yamlconfig(CRED_FILE_PATH)
    doc = buildDoc(CONFIG_FILE_PATH)

    if not os.path.isdir(LOGDIR):
        os.makedirs(LOGDIR)

    wc.save_json(
        doc,
        os.path.join(LOGDIR, 'toSendDoc_{}'.format(time.strftime('%y%m%d-%H%M%S')))
    )
    sendDoc(cred, doc)
