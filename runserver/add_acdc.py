#! /usr/bin/env python

"""
.. describe:: add_acdc.py

A python script that searches the actions database
and adds the list of ACDCs to all previous actions

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

from CMSToolBox import workflowinfo
from WorkflowWebTools import manageactions

if __name__ == '__main__':

    manageactions.serverconfig.LOCATION = '.'
    coll = manageactions.get_actions_collection()

    for workflow in manageactions.get_actions(0):

        print workflow

        prep_id = workflowinfo.WorkflowInfo(workflow).get_prep_id()

        coll.update_one({'workflow': workflow},
                        {'$set': {'parameters.ACDCs':
                                      [wkf for wkf in \
                                           workflowinfo.PrepIDInfo(prep_id).get_workflows() \
                                           if wkf != workflow]}
                        })
