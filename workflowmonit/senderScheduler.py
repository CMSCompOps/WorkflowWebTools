#!/usr/bin/env python
from __future__ import print_function

import os
import time

import schedule
from workflowmonit import sendToMonit as stm

CRED_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credential.yml')
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
LOGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Logs')

schedule.every().hour.do(stm.jobWrapper)


if __name__ == "__main__":

    while True:
        schedule.run_pending()
        time.sleep(1)