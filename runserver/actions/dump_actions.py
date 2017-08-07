#! /usr/bin/env python

"""
.. describe:: dump_actions.py

A transistion tool for putting actions stored in json files into MongoDB.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import time
import glob
import json

from WorkflowWebTools import manageactions

if __name__ == '__main__':

    manageactions.serverconfig.LOCATION = '..'
    coll = manageactions.get_actions_collection()

    for match in glob.iglob('*.json'):
        check_int = match.split('_')[-1].rstrip('.json')
        timestamp = int(time.mktime(time.strptime(check_int, '%Y%m%d')))
        with open(match, 'r') as infile:
            output = json.load(infile)
            for key, value in output.iteritems():
                value['user'] = match.split('/')[-1].split('_')[0]

                coll.update_one({'workflow': key},
                        {'$set':
                             {'timestamp': timestamp,
                              'parameters': value,
                              'acted': 1}},
                        upsert=True)

