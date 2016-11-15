#! /usr/bin/env python


import os
import sys
import json
import httplib
import ssl


def report(*args):
    if not os.path.exists('key.json'):
        print 'Needs to be called from same directory as key.json'
        exit()

    with open('key.json', 'r') as key_file:
        key_info = json.load(key_file)

    conn = httplib.HTTPSConnection(key_info['url'], key_info['port'],
                                   context=ssl._create_unverified_context())

    conn.request(
        'POST', key_info['path'],
        json.dumps({'key': key_info['key'], 'workflows': args}),
        {'Content-type': 'application/json'})

    print conn.getresponse().read()
    conn.close()
    

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Usage: ./report_action.py workflow1 [workflow2 ...]'
        exit()

    report(*sys.argv[1:])
