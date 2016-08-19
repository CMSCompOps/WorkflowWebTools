#!/bin/bash

sudo bash -c "source setenv.sh; nohup python2.7 $(dirname $0)/workflowtools.py &"
