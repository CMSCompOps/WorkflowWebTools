#! /usr/bin/env python

import unittest
import json
import shutil
import os
import sys

import cmstoolbox.webtools
cmstoolbox.webtools.get_json = lambda *a, **k: {}

import workflowwebtools.serverconfig as sc
sc.LOCATION = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'config.yml')

import cmstoolbox._loadtestpath

import update_history as uh
import workflowwebtools.reasonsmanip as rm
import workflowwebtools.manageactions as ma
import workflowwebtools.globalerrors as ge

from workflowwebtools.paramsregression import convert_to_dense

from workflowwebtools.workflowinfo import WorkflowInfo

class TestGlobalError(unittest.TestCase):

    testdat = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'testdat.json')

    dictionary = {
        '/test1/a/1': {
            'errors': {
                'row1': {'col1' : 1}, 
                'row2': {'col2': 1, 
                         'col3': 1}
                },
            'sub': {},
            'total': 3
            },
        '/test1/a/2': {
            'errors': {
                'row1': {'col1' : 1,
                         'col2' : 1}, 
                'row2': {'col3': 1}
                },
            'sub': {},
            'total': 3
            },
        '/test2/a/1': {
            'errors': {
                'row2': {'col1': 1}
                },
            'sub': {},
            'total': 1
            }
        }

    def test_grouping(self):
        group_by = lambda subtask: subtask.split('/')[1]
        check_this = ge.group_errors(self.dictionary, group_by)

        self.assertEqual(len(check_this.keys()), 2)
        self.assertTrue('test1' in check_this.keys())
        self.assertTrue('test2' in check_this.keys())
        self.assertEqual(check_this['test1']['errors'], {'row1': {'col1': 2, 'col2': 1}, 'row2': {'col2': 1, 'col3': 2}})
        self.assertEqual(check_this['test2']['errors'], {'row2': {'col1': 1}})
        self.assertEqual(check_this['test1']['sub']['/test1/a/1'], self.dictionary['/test1/a/1'])

    def test_steplist(self):
        info = ge.ErrorInfo(self.testdat)

        self.assertEqual(info.get_step_list('test1'), ['/test1/a/1', '/test1/a/2'])
        self.assertEqual(info.get_step_list('test2'), ['/test2/a/1'])
        self.assertFalse(info.get_step_list('test3'))

    def test_reset(self):
        info = ge.ErrorInfo(self.testdat)
        # Let's load the new one
        info.data_location = self.testdat.replace('.json', '2.json')
        self.assertFalse(info.get_step_list('test3'))
        info.teardown()
        info.setup()
        self.assertEqual(info.get_step_list('test3'), ['/test3/test/2'])
        self.assertFalse(info.get_step_list('test1'))


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

        ge.check_session(None).data_location = out_name
        ge.check_session(None).setup()

        for wkf in ge.check_session(None).return_workflows():
            file_name = WorkflowInfo(wkf).cache_filename('workflow_params')
            dirname = os.path.dirname(file_name)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(file_name, 'w') as cache:
                json.dump({}, cache)

    def tearDown(self):
        os.remove(sc.workflow_history_path())
        if sc.workflow_history_path() != sc.all_errors_path():
            os.remove(sc.all_errors_path())

        for wkf in ge.check_session(None).return_workflows():
            file_name = WorkflowInfo(wkf).cache_filename('workflow_params')
            os.remove(file_name)

        ge.check_session(None).teardown()

    def test_updatehistory(self):
        import workflowwebtools.globalerrors as ge

        self.assertEqual(ge.ErrorInfo(sc.all_errors_path()).info[1:],
                         ge.ErrorInfo(sc.workflow_history_path()).info[1:],
                         'Update workflow script did not create equivalent database')

    def test_clusterer(self):
        import workflowwebtools.globalerrors as ge
        import workflowwebtools.clusterworkflows as cw

        clusterer = cw.get_clusterer(sc.workflow_history_path())

        for workflow in ge.GLOBAL_INFO.return_workflows():
            self.assertEqual(cw.get_clustered_group(workflow, clusterer),
                             self.should_cluster[workflow],
                             'Clustering acting unexpectedly.')

    def test_steptable(self):
        # This isn't particularly well written,
        # but we should expect a table with
        # rows corresponding to error codes 1, 2, 3 and
        # columns corresponding to site names site_a, site_b, site_c

        allmap = ge.check_session(None).get_allmap()

        for step in self.errors:
            error_table = ge.get_step_table(step)

            # One by hand because weird stuff is happening while writing this test
            if step == '/test1/a/1':
                self.assertEqual(error_table[0][0], 100)

            self.assertTrue(error_table)
            for row in error_table:
                self.assertTrue(row)

            # Check number of rows and errors
            self.assertEqual(len(allmap['errorcode']), len(error_table))
            for e_index, error in enumerate(allmap['errorcode']):
                # Make sure all of the sites have a column
                self.assertEqual(len(allmap['sitename']), len(error_table[e_index]))
                for s_index, site in enumerate(allmap['sitename']):
                    self.assertEqual(error_table[e_index][s_index],
                                     self.errors[step].get(str(error), {}).get(site, 0))

    def test_sparsetodense(self):
        dense = {}
        sparse = {}
        for step in self.errors:
            sparse[step] = ge.get_step_table(step, sparse=True)
            dense[step] = ge.get_step_table(step)

        to_dense = convert_to_dense(sparse, self.errors.keys())

        for step in self.errors:
            self.assertEqual(dense[step], to_dense[step])


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
        if os.path.exists('reasons.db'):
            os.remove('reasons.db')

        print 'before', rm.reasons_list()

        rm.update_reasons(self.reasons)

        print 'after', rm.reasons_list()


    def tearDown(self):
        os.remove('reasons.db')

    def test_reasons(self):

        self.assertRaises(TypeError, rm.update_reasons, 'test')
        self.assertRaises(KeyError, rm.update_reasons, [{'wrong': 'key'}])
        self.assertEqual(rm.reasons_list(),
                         {reas['short']: reas['long'] for reas in self.reasons},
                         'Reasons list return is not same as sent,\n\n%s\n\n%s' %
                         (rm.reasons_list(), {reas['short']: reas['long'] for reas in self.reasons}))


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
        rm.update_reasons(self.reasons1)

        if ma.get_actions_collection().count() != 0:
            print 'Test database not empty, abort!!'
            exit(123)

        file_name = WorkflowInfo(self.request_base['workflows']).cache_filename('workflow_params')
        dirname = os.path.dirname(file_name)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(file_name, 'w') as cache:
            json.dump({}, cache)

    def tearDown(self):
        os.remove('reasons.db')
        ma.get_actions_collection().drop()

        file_name = WorkflowInfo(self.request_base['workflows']).cache_filename('workflow_params')
        os.remove(file_name)

    def run_test(self, request, params_out):

        wf, reasons, params = ma.submitaction('test', **request)

        self.assertEqual(wf, [self.request_base['workflows']],
                         'Workflows is not expected output')
        
        self.assertEqual(reasons,
                         [{'short': 'short reason %i' % i, 'long': 'long reason %i' % i} for i in [2, 3, 1]],
                         'Output reasons are not what are expected')

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

class TestBlankReasons(TestActions):
    def test_blank_short(self):
        request = {
            'workflows': 'test_workflow',
            'action': 'clone',
            'shortreason0': '',
            'longreason0': 'Long reason'
            }

        wf, reasons, params = ma.submitaction('test', **request)
        self.assertEqual(reasons[0]['short'], rm.DEFAULT_SHORT)

    def test_blank_long(self):
        request = {
            'workflows': 'test_workflow',
            'action': 'clone',
            'shortreason0': 'Short Reason',
            'longreason0': ''
            }

        wf, reasons, params = ma.submitaction('test', **request)
        self.assertEqual(reasons[0]['short'], reasons[0]['long'])

if __name__ == '__main__':
    unittest.main()
