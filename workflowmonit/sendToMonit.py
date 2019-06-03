#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import time
import sqlite3
import logging
import threading
import logging.config
try:
    from Queue import Queue
except ImportError:
    from queue import Queue # pylint: disable=import-error

import yaml
from CMSMonitoring.StompAMQ import StompAMQ
import workflowmonit.workflowCollector as wc
import workflowmonit.alertingDefs as ad

CRED_FILE_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'credential.yml')
CONFIG_FILE_PATH = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'config.yml')
LOGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
LOGGING_CONFIG = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'configLogging.yml')


class NotFinished(Exception):
    """ Task unfinished.. """


class TimeoutQueue(Queue):

    def join_with_timeout(self, timeout):
        self.all_tasks_done.acquire()
        try:
            endtime = time.time() + timeout
            while self.unfinished_tasks:
                remaining = endtime - time.time()
                if remaining <= 0.0:
                    raise NotFinished
                self.all_tasks_done.wait(remaining)
        except:
            logger.exception(
                "Unfinished tasks detected (timeout = {}s). won't wait.".format(timeout))
        finally:
            self.all_tasks_done.release()


def worker(res, q, completedWfs, minFailureRate=0., configPath=CONFIG_FILE_PATH):
    """
    Get item from queue, work on it, append result to ``res``.

    :param list res: container to hold results
    :param list completedWfs: completed workflows, to avoid re-caching
    :param TimeoutQueue q: queue
    :param float minFailureRate: minimum failure rate
    :param str configPath: path to config file
    """

    dbPath = wc.get_yamlconfig(configPath).get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'workflow_status.sqlite')
    )
    DB_UPDATE_CMD = """INSERT OR REPLACE INTO workflowStatuses VALUES (?,?,?)"""

    while not q.empty():
        wf = q.get()
        if wf.workflow in completedWfs:
            continue

        try:
            failurerate = wf.get_failure_rate()
            if failurerate > minFailureRate:
                res.append(wc.populate_error_for_workflow(wf))

            toUpdate = (
                wf.workflow,
                wf._get_reqdetail().get(wf.workflow, {}).get('RequestStatus', ''),
                failurerate
            )
            if not all(toUpdate[:-1]):
                continue
            conn = sqlite3.connect(dbPath)
            with conn:
                c = conn.cursor()
                c.execute(DB_UPDATE_CMD, toUpdate)

        except:
            logger.exception(
                'workflow "{}" has trouble caching.'.format(wf.workflow))
            pass
        finally:
            q.task_done()
    return True


def getCompletedWorkflowsFromDb(configPath):
    """
    Get completed workflow list from local status db (setup to avoid unnecessary caching)

    Workflows whose status ends with *archived* are removed from further caching.

    :param str configPath: location of config file
    :returns: list of workflow (str)
    :rtype: list
    """

    config = wc.get_yamlconfig(configPath)
    if not config:
        sys.exit('Config file: {} not exist, exiting..'.format(configPath))
    dbPath = config.get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'workflow_status.sqlite')
    )

    DB_CREATE_CMD = """CREATE TABLE IF NOT EXISTS workflowStatuses (
        name TEXT PRIMARY KEY,
        status TEXT,
        failurerate REAL
    );"""
    DB_QUERY_CMD = """SELECT * FROM workflowStatuses WHERE status LIKE '%archived'"""

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
    update workflow status to local status db, with the information from ``wcErrorInfos``.

    :param str configPath: location of config file
    :param list wcErrorInfos: list of dicts returned by :py:func:`wc.filter_n_collect`
    :returns: True
    """

    config = wc.get_yamlconfig(configPath)
    if not config:
        sys.exit('Config path: {} not exist, exiting..'.format(configPath))
    dbPath = config.get(
        'workflow_status_db',
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'workflow_status.sqlite')
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
        if not all(entry[:-1]):
            continue
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

    logger.info('Number of workflows to query: {}'.format(len(wkfs)))

    wc.invalidate_caches('/tmp/wsi/workflowinfo')

    results = list()

    q = TimeoutQueue(maxsize=500)
    num_threads = 500
    for i, wf in enumerate(wkfs, 1):
        q.put(wf)
        if q.full() or i==len(wkfs):
            for _ in range(num_threads):
                t = threading.Thread(target=worker, args=(results, q, completedWfs, ))
                t.daemon = True
                t.start()
            try:
                q.join_with_timeout(30*60)  # timeout 30min
            except NotFinished:
                pass

    updateWorkflowStatusToDb(configpath, results)
    logger.info('Number of updated workflows: {}'.format(len(results)))

    return results


def sendDoc(cred, docs):
    """
    Given a credential dict and documents to send, make notification.

    :param dict cred: credential required by StompAMQ
    :param list docs: documents to send
    :returns: None
    """

    if not docs:
        logger.info("No document going to be set to AMQ.")
        return []

    try:
        amq = StompAMQ(
            username = None,
            password = None,
            producer = cred['producer'],
            topic = cred['topic'],
            validation_schema = None,
            host_and_ports=[
                (cred['hostport']['host'], cred['hostport']['port'])],
            logger=logger,
            cert=cred['cert'],
            key=cred['key']
        )

        doctype = 'workflowmonit_{}'.format(cred['producer'])
        notifications = [amq.make_notification(
            payload=doc, docType=doctype)[0] for doc in docs]
        failures = amq.send(notifications)

        logger.info("{}/{} docs successfully sent to AMQ.".format(
            (len(notifications)-len(failures)), len(notifications)))
        return failures

    except Exception as e:
        logger.exception(
            "Failed to send data to StompAMQ. Error: {}".format(str(e)))
        raise


def main():

    recipients = wc.get_yamlconfig(CONFIG_FILE_PATH).get('alert_recipients', [])

    try:
        with open(LOGGING_CONFIG, 'r') as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)

        global logger
        logger = logging.getLogger('workflowmonitLogger')

        cred = wc.get_yamlconfig(CRED_FILE_PATH)
        docs = buildDoc(CONFIG_FILE_PATH)

        # handling alerts
        ad.alertWithEmail(docs, recipients)

        # backup documents
        if not os.path.isdir(LOGDIR):
            os.makedirs(LOGDIR)

        doc_bkp = os.path.join(LOGDIR, 'toSendDoc_{}'.format(
            time.strftime('%y%m%d-%H%M%S')))
        docfn = wc.save_json(docs, filename=doc_bkp, gzipped=True)
        logger.info('Document saved at: {}'.format(docfn))

        failures = sendDoc(cred=cred, docs=docs)

        failedDocs_bkp = os.path.join(
            LOGDIR, 'amqFailedMsg_{}'.format(time.strftime('%y%m%d-%H%M%S')))
        if len(failures):
            failedDocFn = wc.save_json(failures, filename=failedDocs_bkp, gzipped=True)
            logger.info('Failed message saved at: {}'.format(failedDocFn))
    except Exception as e:
        logger.exception("Exception encounted, sending emails to {}".format(str(recipients)))
        ad.errorEmailShooter(str(e), recipients)


if __name__ == "__main__":
    main()
