#!/usr/bin/env python
from __future__ import print_function
import os
import yaml
import socket
import time
import workflowCollector
from workflowwebtools import workflowinfo
from WMCore.Services.StompAMQ.StompAMQ import StompAMQ

CRED_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credential.yml')
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')


def buildDoc(configpath):
    """
    Given a path to the config file which contains oracle db connection info,
    returns a list of documents (each for one workflow)

    :param str configpath: location of config file
    :returns: list of documents

    :rtype: list
    """

    DB_QUERY_CMD = "SELECT NAME FROM CMS_UNIFIED_ADMIN.WORKFLOW WHERE WM_STATUS LIKE 'running%'"

    wkfs = workflowCollector.get_workflow_from_db(configpath, DB_QUERY_CMD)

    result = []
    for wf in wkfs:
        result.append(
                workflowCollector.populate_error_for_workflow(wf)
                )

    return result


def send(cred, doc):
    """
    Given a credential dict and documents to send, make notification.

    :param dict cred: credential required by StompAMQ
    :param list doc: documents to send
    :returns: None
    """

    host, port = cred['host_and_ports'].split(':')
    port = int(port)

    amq = StompAMQ(
            cred['usename'],
            cred['password'],
            cred['producer'],
            cred['topic'],
            [(host, port)]
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

    cred = workflowCollector.get_yamlconfig(CRED_FILE_PATH)
    workflowCollector.invalidate_caches()
    doc = buildDoc(CONFIG_FILE_PATH)
    
    send(cred, doc)
