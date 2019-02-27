#!/usr/bin/env python
from __future__ import print_function

import os
import time

import schedule
import workflowmonit.sendToMonit as wms

CRED_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credential.yml')
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
LOGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')
LOGGING_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configLogging.yml')

schedule.every().hour.do(wms.main)


if __name__ == "__main__":

    while True:
        schedule.run_pending()
        time.sleep(1)
