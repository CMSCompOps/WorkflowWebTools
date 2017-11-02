#! /usr/bin/env python

import unittest
import json
import shutil
import os
import sys

import WorkflowWebTools.serverconfig as sc
sc.LOCATION = os.path.dirname(os.path.realpath(__file__))

import CMSToolBox._loadtestpath

import update_history as uh
import WorkflowWebTools.reasonsmanip as rm
import WorkflowWebTools.manageactions as ma
import WorkflowWebTools.globalerrors as ge


class TestGlobalError(unittest.TestCase):

    dictionary = {
        '/test1/a/1': {
            'errors': [[1, 0, 0], [0, 1, 1]],
            'sub': {}
            },
        '/test1/a/2': {
            'errors': [[1, 1, 0], [0, 0, 1]],
            'sub': {}
            },
        '/test2/a/1': {
            'errors': [[0, 0, 0], [1, 0, 0]],
            'sub': {}
            }
        }

    def test_grouping(self):
        group_by = lambda subtask: subtask.split('/')[1]
        check_this = ge.group_errors(self.dictionary, group_by)

        self.assertEqual(len(check_this.keys()), 2)
        self.assertTrue('test1' in check_this.keys())
        self.assertTrue('test2' in check_this.keys())
        self.assertEqual(check_this['test1']['errors'], [[2, 1, 0], [0, 1, 2]])
        self.assertEqual(check_this['test2']['errors'], [[0, 0, 0], [1, 0, 0]])
        self.assertEqual(check_this['test1']['sub']['/test1/a/1'], self.dictionary['/test1/a/1'])


class TestClusteringAndReasons(unittest.TestCase):

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
            },
        '/crash/time/haha': {
            'NotANumber': {
                'site_c': 0
                }
            }
        }

    should_cluster = {
        'test1' : ['test2'],
        'test2' : ['test1'],
        'test3' : []
        }
            
    def setUp(self):
        out_name = sc.all_errors_path()

        if not os.path.exists(os.path.dirname(out_name)):
            os.makedirs(os.path.dirname(out_name))

        with open(sc.all_errors_path(), 'w') as output:
            json.dump(self.errors, output)

        if sc.workflow_history_path() != sc.all_errors_path():
            uh.main(sc.all_errors_path())

    def tearDown(self):
        os.remove(sc.workflow_history_path())
        if sc.workflow_history_path() != sc.all_errors_path():
            os.remove(sc.all_errors_path())

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

    def setUp(self):
        rm.LOCATION = os.path.join(sc.LOCATION, 'test')
        if not os.path.exists(rm.LOCATION):
            os.makedirs(rm.LOCATION)

        rm.update_reasons(self.reasons)

    def tearDown(self):
        shutil.rmtree(rm.LOCATION)
        rm.LOCATION = sc.LOCATION

    def test_reasons(self):

        self.assertRaises(TypeError, rm.update_reasons, 'test')
        self.assertRaises(KeyError, rm.update_reasons, [{'wrong': 'key'}])
        print rm.reasons_list()
        print {reas['short']: reas['long'] for reas in self.reasons}
        self.assertEqual(rm.reasons_list(),
                         {reas['short']: reas['long'] for reas in self.reasons},
                         'Reasons list return is not same as sent')


class TestActions(unittest.TestCase):

    reasons1 = [
        {
            'short': 'short reason 1',
            'long': 'long reason 1'
        }
    ]

    reasons2 = {
        'shortreason0': 'short reason 2',
        'longreason0': 'long reason 2',
        'shortreason4': 'short reason 3',
        'longreason4': 'long reason 3',
        'selectedreason': 'short reason 1',
    }

    request_base = {
        'workflows': 'test_workflow',
        'task_0': 'task/0',
        'task_1': 'task/1',
    }

    def extend_request(self, request):
        output = request
        output.update(self.reasons2)
        output.update(self.request_base)

        return output

    def setUp(self):
        rm.LOCATION = os.path.join(sc.LOCATION, 'test')
        if not os.path.exists(rm.LOCATION):
            os.makedirs(rm.LOCATION)

        rm.update_reasons(self.reasons1)

        if ma.get_actions_collection().count() != 0:
            print 'Test database not empty, abort!!'
            exit(123)

    def tearDown(self):
        shutil.rmtree(rm.LOCATION)
        rm.LOCATION = sc.LOCATION
        ma.get_actions_collection().drop()

    def run_test(self, request, params_out):

        wf, reasons, params = ma.submitaction('test', **request)

        print wf
        print [self.request_base['workflows']]

        self.assertEqual(wf, [self.request_base['workflows']],
                         'Workflows is not expected output')
        
        print reasons
        print [{'short': 'short reason %i' % i, 'long': 'long reason %i' % i} for i in [2, 3, 1]]

        self.assertEqual(reasons,
                         [{'short': 'short reason %i' % i, 'long': 'long reason %i' % i} for i in [2, 3, 1]],
                         'Output reasons are not what are expected')

        print params
        print params_out

        self.assertEqual(params, params_out,
                         'Parameters out are not expected')

    def test_clone(self):
        request = self.extend_request({
                'action': 'clone',
                'param_0_test': 'test_param'
                })
        self.run_test(request, {'test': 'test_param'})

    def test_acdc(self):
        request = self.extend_request({
                'action': 'acdc',
                'param_0_test': 'test_param_0',
                'param_1_test': 'test_param_1',
                })
        self.run_test(request, {'task/0': {'test': 'test_param_0'},
                                'task/1': {'test': 'test_param_1'}})

    def test_investigate(self):
        request = self.extend_request({
                'action': 'investigate',
                'param_0_test': 'test_param'
                })
        self.run_test(request, {'test': 'test_param'})

if __name__ == '__main__':
    unittest.main()
