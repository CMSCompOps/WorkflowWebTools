#!/usr/bin/env python
from __future__ import print_function
import time
import json
import smtplib
from email.mime.text import MIMEText


def onFailureRate(doc, thres=0.5):
    """
    check a workflow (represented by `doc`), if its failureRate is larger than
    0.5 AND running time is > 2days, then ALERT.

    :param doc dict: information describe a workflow
    :param thres float: threshold
    :returns: (judge result, short msg if failed)
    """

    res = (False, '')
    if doc['status'] != 'running-open': return res
    if doc['failureRate'] < thres: return res
    runningOpen = [
        tr for tr in doc['transitions'] if tr['Status'] == 'running-open'
    ]
    if not runningOpen: return res

    runningOpenTime = runningOpen[0]['UpdateTime']
    if time.time() - runningOpenTime < 2 * 24 * 60 * 60: return res

    failMsg = 'FailureRate ({}) larger than threshold({}), while running time over 2 days (started at {})'.format(
        doc['failureRate'], thres, time.ctime(runningOpenTime))

    return (True, failMsg)


AlertDefs = [
    onFailureRate,
]


def alertWithEmail(docs, recipients):
    """
    handling docs with alert emails.


    :param docs list: list of documents
    :param recipients list: list of recipients email addresses
    """

    sender = 'toolsandint-workflowmonitalert@cern.ch'

    for doc in docs:
        alertResults = [ad(doc) for ad in AlertDefs]
        positiveRes = [r for r in alertResults if r[0]]
        if positiveRes:
            shortAlertMsgs = [x[1] for x in positiveRes]
            _contentMsg = '\n\n'.join([
                '*** THIS IS A GENERATED MESSAGE, PLEASE DO NOT REPLY ***',
                'Workflow: {}'.format(doc['name']),
                'Short Summary:\n{}'.format('\n'.join([
                    '- {}'.format(s) for s in shortAlertMsgs
                ])),
                '-'* 79,
                'Full document:\n{}'.format(
                    json.dumps(
                        doc, sort_keys=True, indent=4, separators=(',', ': ')))
            ])

            contentMsg = MIMEText(_contentMsg)
            contentMsg['Subject'] = '[workflowmonit] Alert on * {} *'.format(
                doc['name'])
            contentMsg['From'] = sender
            contentMsg['To'] = ', '.join(recipients)
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, recipients, contentMsg.as_string())
            s.quit()


def errorEmailShooter(msg, recipients):
    """
    forward the error message to recipients by emails

    :param msg str: error mesages
    :param recipients list: list of recipients email address
    """

    sender = 'toolsandint-workflowmonitalert@cern.ch'

    contentMsg = MIMEText(msg)
    contentMsg['Subject'] = 'Exception caught for workflowmonit'
    contentMsg['From'] = sender
    contentMsg['To'] = ', '.join(recipients)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipients, contentMsg.as_string())
    s.quit()


def main():

    import os
    testdoc = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'Logs/toSendDoc_190317-033802.json')
    docs = json.load(open(testdoc))
    print([(d['name'], d['failureRate']) for d in docs])

    alertWithEmail(docs, ['weinan.si@cern.ch', ])



if __name__ == "__main__":
    main()
