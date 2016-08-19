# Add path for python2.7

export PATH=/usr/local/bin:$PATH

# Add OpsSpace to the PYTHONPATH

target=`pwd`
target=${target%%/WorkflowWebTools/runserver}

export PYTHONPATH=$PYTHONPATH:$target
