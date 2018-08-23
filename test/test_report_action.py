#! /usr/bin/env python

"""
Test the different responses that reporting an action could do
"""

import os
import time
import unittest

import cmstoolbox.webtools
cmstoolbox.webtools.get_json = lambda *a, **k: {}

from workflowwebtools import serverconfig
serverconfig.LOCATION = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'config.yml')

from workflowwebtools import manageactions

class TestReportResponse(unittest.TestCase):
    new_workflows = ['test_workflow_1', 'test_workflow_2', 'new_test']
    old_workflows = ['old_workflow_1', 'old_workflow_2']
    fake_workflows = ['does_not_exist', 'not_workflow']

    def setUp(self):
        self.output = {}
        self.coll = manageactions.get_actions_collection()
        # Check that test database is empty
        if self.coll.count() != 0:
            print 'Test database not empty, abort!!'
            exit(123)

        now = time.time()
        # Add the workflows that we want to say exists
        for acted, workflows in [(0, self.new_workflows), (1, self.old_workflows)]:
            for wf in workflows:
                self.coll.insert_one({'workflow': wf, 'acted': acted, 'timestamp': now, 'parameters': {}})

    def tearDown(self):
        self.coll.drop()

    def test_setup(self):
        self.assertEqual(self.coll.count(), len(self.new_workflows + self.old_workflows))
        self.assertEqual(sorted(self.new_workflows),
                         sorted(manageactions.get_actions(acted=0).keys()))
        self.assertEqual(sorted(self.old_workflows),
                         sorted(manageactions.get_actions(acted=1).keys()))

    def test_new(self):
        manageactions.report_actions(self.new_workflows, self.output)

        self.assertEqual(sorted(self.new_workflows), sorted(self.output['success']))
        self.assertFalse(self.output['already_reported'])
        self.assertFalse(self.output['does_not_exist'])

    def test_old(self):
        manageactions.report_actions(self.old_workflows, self.output)

        self.assertFalse(self.output['success'])
        self.assertEqual(sorted(self.old_workflows), sorted(self.output['already_reported']))
        self.assertFalse(self.output['does_not_exist'])

    def test_not_exist(self):
        manageactions.report_actions(self.fake_workflows, self.output)

        self.assertFalse(self.output['success'])
        self.assertFalse(self.output['already_reported'])
        self.assertEqual(sorted(self.fake_workflows), sorted(self.output['does_not_exist']))

    def test_everything(self):
        manageactions.report_actions(self.new_workflows + 
                                     self.old_workflows +
                                     self.fake_workflows, self.output)

        self.assertEqual(sorted(self.new_workflows), sorted(self.output['success']))
        self.assertEqual(sorted(self.new_workflows), sorted(self.output['success']))
        self.assertEqual(sorted(self.fake_workflows), sorted(self.output['does_not_exist']))


if __name__ == '__main__':
    unittest.main()
