#!/bin/bash

##!
# .. describe:: run.sh
#
# :author: Daniel Abercrombie <dabercro@mit.edu>
#
# This simple script launches the ``workflowtools.py`` in the background as root.
# Make sure that ``setenv.sh`` correctly adjusts the user's ``$PATH`` and
# ``$PYTHONPATH`` to run the tool.
##!

sudo bash -c "source setenv.sh; nohup python2.7 $(dirname $0)/workflowtools.py &"
