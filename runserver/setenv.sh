#! /bin/bash

# Add OpsSpace to the PYTHONPATH

target=$(pwd)
target=${target%%/WorkflowWebTools/runserver}

export PYTHONPATH=$target:$target/local/lib/python2.7/site-packages:$PYTHONPATH

export X509_USER_PROXY=/tmp/x509up_u${UID}
source /data/srv/wmagent/current/apps/wmagent/etc/profile.d/init.sh
