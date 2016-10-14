#! /usr/bin/env python

import unittest
import json
import os
import sys

import WorkflowWebTools.serverconfig as sc
sc.LOCATION = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(sc.LOCATION, '../runserver'))

import update_history as uh
import WorkflowWebTools.reasonsmanip as rm

class TestGlobalInfo(unittest.TestCase):

    errors = {
        '/test1/a/1': {
            '1': {
                'site_a': 100
                },
            '2': {
                'site_a': 10,
                'site_b': 100
                },
            },
        '/test2/a/2': {
            '1': {
                'site_a': 90
                },
            '2': {
                'site_a': 10,
                'site_b': 100
                },
            },
        '/test3/b/a': {
            '3': {
                'site_c': 50
                }
            }
        }

    should_cluster = {
        'test1' : ['test2'],
        'test2' : ['test1'],
        'test3' : []
        }        
            
    explained = {
        '1': [
            'Error 1',
            'Still Error 1'
            ],
        '2': [
            'Error 2'
            ],
        '3': [
            'Different Error'
            ]
        }

    def setUp(self):
        out_name = sc.all_errors_path()

        if not os.path.exists(os.path.dirname(out_name)):
            os.makedirs(os.path.dirname(out_name))

        with open(sc.all_errors_path(), 'w') as output:
            json.dump(self.errors, output)

        with open(sc.explain_errors_path(), 'w') as output:
            json.dump(self.explained, output)

        if sc.workflow_history_path() != sc.all_errors_path():
            uh.main(sc.all_errors_path())

    def tearDown(self):
        os.remove(sc.workflow_history_path())

    def test_updatehistory(self):
        import WorkflowWebTools.globalerrors as ge

        self.assertEqual(ge.ErrorInfo(sc.all_errors_path()).info[1:],
                         ge.ErrorInfo(sc.workflow_history_path()).info[1:],
                         'Update workflow script did not create equivalent database')

    def test_clusterer(self):
        import WorkflowWebTools.globalerrors as ge
        import WorkflowWebTools.clusterworkflows as cw

        clusterer = cw.get_clusterer(sc.workflow_history_path())

        for workflow in ge.GLOBAL_INFO.return_workflows():
            self.assertEqual(cw.get_clustered_group(workflow, clusterer),
                             self.should_cluster[workflow],
                             'Clustering acting unexpectedly.')

class TestReasons(unittest.TestCase):

    reasons = [
        {
            'short': 'short reason 1',
            'long': 'secretly long reason'
        },
        {
            'short': 'short reason 2',
            'long': 'another secretly long reason'
        }
    ]

    rm.LOCATION = os.path.join(sc.LOCATION, 'test')

    def setUp(self):
        if not os.path.exists(rm.LOCATION):
            os.makedirs(rm.LOCATION)

        rm.update_reasons(self.reasons)

    def tearDown(self):
        os.remove(os.path.join(rm.LOCATION, 'reasons.db'))

    def test_reasons(self):

        self.assertRaises(TypeError, rm.update_reasons, 'test')
        self.assertRaises(KeyError, rm.update_reasons, [{'wrong': 'key'}])
        self.assertEqual(rm.reasons_list(), 
                         {reas['short']: reas['long'] for reas in self.reasons},
                         'Reasons list return is not same as sent')


if __name__ == '__main__':
    unittest.main()
