"""
Defines the class that runs the server
"""

# pylint: disable=no-member, no-self-use, invalid-name

# Definitely clean these
# pylint: disable=too-many-public-methods, missing-docstring, attribute-defined-outside-init


import json
import time
import datetime
import threading
import sqlite3

import cherrypy

from cmstoolbox import sitereadiness

from workflowwebtools import workflowinfo
from workflowwebtools import serverconfig
from workflowwebtools import manageactions
from workflowwebtools import manageusers
from workflowwebtools import showlog
from workflowwebtools import reasonsmanip
from workflowwebtools import listpage
from workflowwebtools import globalerrors
from workflowwebtools import clusterworkflows
from workflowwebtools import classifyerrors
from workflowwebtools import actionshistorylink
from workflowwebtools.web.templates import render
from workflowwebtools.predict import evaluate

from workflowwebtools import statuses


class WorkflowTools(object):

    RESET_LOCK = threading.Lock()

    def __init__(self):
        self.lock = threading.Lock()
        self.wflock = threading.Lock()
        self.readinesslock = threading.Lock()
        self.seeworkflowlock = threading.Lock()
        self.cluster()
        self.update()

        self.markedreset = set()


    @cherrypy.expose
    def markreset(self, prepid):
        self.lock.acquire()
        self.markedreset.add(prepid)
        self.lock.release()

    def reset(self):

        self.lock.acquire()
        # Reset things is requested
        if self.markedreset:
            for pid in self.markedreset:
                for wf in self.prepids[pid].get_workflows():
                    self.wflock.acquire()
                    workflow_obj = self.workflows.pop(wf, None)
                    self.wflock.release()
                    if workflow_obj:
                        workflow_obj.reset()

                prep_obj = self.prepids.pop(pid, None)
                if prep_obj:
                    prep_obj.reset()

            self.markedreset = set()
        self.lock.release()



    def update(self):

        self.lock.acquire()
        self.workflows = {}

        try:
            for workflow in statuses.get_manual_workflows(
                    serverconfig.config_dict()['data']['all_errors']):
                self.get(workflow)

            self.prepids = {
                prepid: workflowinfo.PrepIDInfo(prepid) for prepid in
                [info.get_prep_id() for info in self.workflows.values()]
            }

            self.update_statuses()

        finally:
            self.lock.release()


    def update_statuses(self):
        coll = manageactions.get_actions_collection()
        self.site_statuses = None
        self.statuses = {
            record['workflow']: record['acted']
            for record in coll.find()
            }

    @cherrypy.expose
    def index(self):
        """
        :returns: The welcome page
        :rtype: str
        """
        return render('welcome.html')

    @cherrypy.expose
    def cluster(self):
        """
        The function is only accessible to someone with a verified account.

        Navigating to ``https://localhost:8080/cluster``
        causes the server to regenerate the clusters that it has stored.
        This is useful when the history database of past errors has been
        updated with relevant errors since the server has been started or
        this function has been called.

        :returns: a confirmation page
        :rtype: str
        """
        data = serverconfig.config_dict()['data']
        self.clusterer = clusterworkflows.get_clusterer(
            data['workflow_history'], data['all_errors'])
        return render('complete.html')

    @cherrypy.expose
    def showlog(self, search='', module='', limit=50):
        """
        This page, located at ``https://localhost:8080/showlog``,
        returns logs that are stored in an elastic search server.
        If directed here from :ref:`workflow-view-ref`, then
        the search will be for the relevant workflow.

        :param str search: The search string
        :param str module: The module to look at, if only interested in one
        :param int limit: The limit of number of logs to show on a single page
        :returns: the logs from elastic search
        :rtype: str
        """
        logdata = showlog.give_logs(search, module, int(limit))
        if isinstance(logdata, dict):
            return render('showlog.html',
                          logdata=logdata,
                          search=search,
                          module=module,
                          limit=limit)

        return logdata

    @cherrypy.expose
    def globalerror2(self, reset=False):
        if reset:
            self.reset()
            self.update()

        return render(
            'globalerror2.html'
            )

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getprepids(self):
        return sorted(self.prepids.keys())


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def predict(self, workflow):
        return evaluate.predict(self.get(workflow))

    def get_status(self, workflow):
        status = self.statuses.get(workflow)
        if status is None:
            return "none"
        return "acted" if status else "pending"

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getstatus(self, workflow):
        return {'status': self.get_status(workflow).capitalize()}

    def get(self, workflow):
        self.wflock.acquire()
        wkflow_obj = self.workflows.get(workflow)
        if wkflow_obj is None:
            self.workflows[workflow] = workflowinfo.WorkflowInfo(workflow)
            wkflow_obj = self.workflows[workflow]

        self.wflock.release()
        return wkflow_obj


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getworkflows(self, prepid):
        workflow_objs = {
            workflow: {
                'obj': self.get(workflow),
                'time': requesttime
                }
            for workflow, requesttime in
            self.prepids[prepid].get_workflows_requesttime()
            }

        workflows = [
            {"workflow": workflow,
             "status": self.get_status(workflow),
             "errors": obj['obj'].sum_errors()
            }
            for workflow, obj in workflow_objs.iteritems()
            ]

        self.lock.acquire()
        for workflow, obj in workflow_objs.iteritems():
            if workflow not in self.workflows:
                self.workflows[workflow] = obj['obj']
        self.lock.release()

        return sorted(
            [wkflow for wkflow in workflows if wkflow['errors']],
            key=lambda wkfl: workflow_objs[wkfl['workflow']]['time']
        )


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def submit2(self):
        input_json = cherrypy.request.json
        manageactions.submit2(input_json['documents'])
        self.update_statuses()
        return {'message': 'Done'}


    @cherrypy.expose
    def globalerror(self, pievar='errorcode'):
        """
        This page, located at ``https://localhost:8080/globalerror``,
        attempts to give an overall view of the errors that occurred
        in each workflow at different sites.
        The resulting view is a table of piecharts.
        The rows and columns can be adjusted to contain two of the following:

        - Workflow step name
        - Site where error occurred
        - Exit code of the error

        The third variable is used to split the pie charts.
        This variable inside the pie charts can be quickly changed
        by submitting the form in the upper left corner of the page.

        The size of the piecharts depend on the total number of errors in a given cell.
        Each cell also has a tooltip, giving the total number of errors in the piechart.
        The colors of the piecharts show the splitting based on the ``pievar``.
        Clicking on the pie chart will show the splitting explicitly
        using the :ref:`list-wfs-ref` page.

        If the steps make up the rows,
        the default view will show you the errors for each campaign.
        Clicking on the campaign name will cause the rows to expand
        to show the original workflow and all ACDCs (whether or not the ACDCs have errors).
        Following the link of the workflow will bring you to :ref:`workflow-view-ref`.
        Clicking anywhere else in the workflow box
        will cause it to expand to show errors for each step.

        :param str pievar: The variable that the pie charts are split into.
                           Valid values are:

                           - errorcode
                           - sitename
                           - stepname

        :returns: the global views of errors
        :rtype: str
        """

        # For some reasons, we occasionally have to refresh this global errors page

        errors = globalerrors.get_errors(pievar, cherrypy.session)
        if pievar != 'stepname':

            # This pulls out the timestamp from the workflow parameters
            timestamp = lambda wkf: time.mktime(
                datetime.datetime(
                    *(globalerrors.check_session(cherrypy.session).\
                          get_workflow(wkf).get_workflow_parameters()['RequestDate'])).timetuple()
                )

            errors = globalerrors.group_errors(
                globalerrors.group_errors(errors, lambda subtask: subtask.split('/')[1],
                                          timestamp=timestamp),
                lambda workflow: globalerrors.check_session(cherrypy.session).\
                    get_workflow(workflow).get_prep_id()
                )

        # Get the names of the columns
        cols = globalerrors.check_session(cherrypy.session).\
            get_allmap()[globalerrors.get_row_col_names(pievar)[1]]

        get_names = lambda x: [globalerrors.TITLEMAP[name]
                               for name in globalerrors.get_row_col_names(x)]

        template = lambda: render(
            'globalerror.html',
            errors=errors,
            decoder=json.dumps,
            columns=cols,
            pievar=pievar,
            acted_workflows=manageactions.get_acted_workflows(
                serverconfig.get_history_length()),
            readiness=globalerrors.check_session(cherrypy.session).readiness,
            get_names=get_names
            )

        try:
            return template()
        # I don't remember what kind of exception this throws...
        except Exception: # pylint: disable=broad-except
            time.sleep(1)
            return template()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getreasons(self):
        return [
            {
                'short': shortreason,
                'long': longreason
            }
            for shortreason, longreason in
            sorted(reasonsmanip.reasons_list().iteritems())
        ]


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def workflowerrors(self, workflow):
        wkflow_obj = self.get(workflow)

        errors = wkflow_obj.get_errors(True)
        output = []

        # Need to track total sites, so we need to do nested loops here
        for step, ecs in sorted(errors.iteritems()):
            allsites = set()

            codes = []
            for code, sites in sorted([
                    (-1 if code == 'NotReported' else int(code), sites)
                    for code, sites in ecs.iteritems()]):

                sites = {
                    site: (num or int(code < 0))
                    for site, num in sorted(sites.iteritems())
                }
                allsites.update(sites.keys())

                codes.append({
                    'code': code,
                    'sites': sites
                })

            output.append({
                'step': step,
                'codes': codes,
                'allsites': sorted(allsites)
            })

        return output


    @cherrypy.expose
    def seeworkflow2(self, workflow):
        return render(
            'workflowtables2.html',
            workflow=workflow
            )

    @cherrypy.expose
    def seeworkflow(self, workflow='', issuggested=''):
        """
        Located at ``https://localhost:8080/seeworkflow``,
        this shows detailed tables of errors for each step in a workflow.

        For the exit codes in each row, there is a link to view some of the output
        of the error message for jobs having the given exit code.
        This should help operators understand what the error means.

        At the top of the page, there are links back for :ref:`global-view-ref`,
        :ref:`show-logs-ref`, related JIRA tickets,
        and ReqMgr2 information about the workflow and prep ID.

        The main function of this page is to submit actions.
        Note that you will need to register in order to actually submit actions.
        See :ref:`new-user-ref` for more details.
        Depending on which action is selected, a menu will appear
        for the operator to adjust parameters for the workflows.

        Under the selection of the action and parameters, there is a button
        to show other workflows that are similar to the selected workflow,
        according to the :ref:`clustering-ref`.
        Each entry is a link to open a similar workflow view page in a new tab.
        The option to submit actions will not be on this page though
        (so that you can focus on the first workflow).
        If you think that a workflow in the cluster should have the same actions
        applied to it as the parent workflow,
        then check the box next to the workflow name before submitting the action.

        Finally, before submitting, you can submit reasons for your action selection.
        Clicking the Add Reason button will give you an additional reason field.
        Reasons submitted are stored based on the short reason you give.
        You can then select past reasons from the drop down menu to save time in the future.
        If you do not want to store your reason, do not fill in the Short Reason field.
        The long reason will be used for logging
        and communicating with the workflow requester (eventually).

        :param str workflow: is the name of the workflow to look at
        :param str issuggested: is a string to tell if the page
                                has been linked from another workflow page
        :returns: the error tables page for a given workflow
        :rtype: str
        :raises: 404 if a workflow doesn't seem to be in assistance anymore
                 Resets personal cache in the meanwhile, just in case
        """

        self.seeworkflowlock.acquire()

        output = ''

        try:
            if workflow not in \
                    globalerrors.check_session(
                            cherrypy.session, can_refresh=True).return_workflows():
                WorkflowTools.RESET_LOCK.acquire()
                info = globalerrors.check_session(cherrypy.session)
                if info:
                    info.teardown()
                    info.setup()
                WorkflowTools.RESET_LOCK.release()

                raise cherrypy.HTTPError(404)

            workflowdata = globalerrors.see_workflow(workflow, cherrypy.session)

            drain_statuses = {sitename: drain for sitename, _, drain in \
                                  sitereadiness.i_site_readiness()}

            output = render(
                'workflowtables.html',
                workflowdata=workflowdata,
                workflow=workflow,
                issuggested=issuggested,
                workflowinfo=globalerrors.check_session(cherrypy.session).get_workflow(workflow),
                readiness=globalerrors.check_session(cherrypy.session).readiness,
                drain_statuses=drain_statuses,
                last_submitted=manageactions.get_datetime_submitted(workflow)
                )
        finally:
            self.seeworkflowlock.release()

        return output


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def wkfparams(self, workflow):
        """
        Get the workflow parameters
        :param str workflow: The workflow that we need parameters for
        :returns: Parameters for this workflow
        :rtype: JSON
        """

        return self.get(workflow).get_workflow_parameters()


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def drainstatuses(self):
        """
        :returns: An object (dictionary) of drain statuses of sites
        :rtype: JSON
        """
        return {sitename: drain for sitename, _, drain in \
                    sitereadiness.i_site_readiness()}


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sitestatuses(self):
        """
        :returns: An object (dictionary) of drain statuses of sites
        :rtype: JSON
        """

        self.readinesslock.acquire()

        try:
            if self.site_statuses is None:
                self.site_statuses = [
                    {
                        'site': site,
                        'status': status,
                        'drain': drain
                    }
                    for site, status, drain in sitereadiness.i_site_readiness()
                ]
        finally:
            self.readinesslock.release()

        return self.site_statuses


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def submissionparams(self, workflow):

        wkfl_obj = self.get(workflow)
        steps = sorted(wkfl_obj.get_errors())

        return {
            'submitted': str(manageactions.get_datetime_submitted(workflow)),
            'steps': steps,
            'sitestorun': {
                step: wkfl_obj.site_to_run(step) for step in steps
            },
            'allsites': sorted(
                [{'site': site['site'], 'drain': site['drain']}
                 for site in self.sitestatuses()],
                key=lambda s: s['site']
            )
        }


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def similarwfs(self, workflow):
        """
        Gives back a list of workflows that are clustered with the queried workflow.
        This is just an array of strings.

        :param str workflow: The workflow to find the group.
        :returns: List of similar workflows.
                  If the quey is not a valid workflow in the system, an empty list is returned
        :rtype: JSON
        """
        output = {'similar': [], 'acted': []}

        self.seeworkflowlock.acquire()

        try:
            if workflow in \
                    globalerrors.check_session(cherrypy.session,
                                               can_refresh=True).return_workflows():

                clusterworkflows.CLUSTER_LOCK.acquire()

                similar_wfs = clusterworkflows.\
                    get_clustered_group(workflow, self.clusterer, cherrypy.session)

                clusterworkflows.CLUSTER_LOCK.release()

                acted = [
                    wf for wf in manageactions.get_acted_workflows(
                        serverconfig.get_history_length()) if wf in similar_wfs
                ]

                output = {'similar': sorted(list(similar_wfs)),
                          'acted': acted}
        finally:
            self.seeworkflowlock.release()

        return output


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def classifyerror(self, workflow):
        """
        :returns: An object full of informaton about the workflow errors.
                  The keys are the following:

                  - ``maxerror`` -- The error code that occurred most frequently for the workflow
                  - ``types`` -- Types of errors and exit codes
                  - ``recommended`` -- Recommended actions
                  - ``params`` -- Additional parameters to do actions

        :rtype: JSON
        """

        output = {}
        self.seeworkflowlock.acquire()

        try:
            max_error = classifyerrors.get_max_errorcode(self.get(workflow))
            main_error_class = classifyerrors.classifyerror(max_error, self.get(workflow))

            output = {
                'maxerror': max_error,
                'types': main_error_class[0],
                'recommended': main_error_class[1],
                'params': main_error_class[2]
            }

        finally:
            self.seeworkflowlock.release()

        return output


    @cherrypy.expose
    @cherrypy.tools.json_in()
    def update_reasons(self, reasons):
        reasonsmanip.update_reasons(reasons)
        return 'OK'


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sitesfortasks(self, **kwargs):
        """
        Accessed through a popup that allows user to submit sites for workflow
        tasks that did not have any sites to run on.
        Returns operators back the :py:func:`get_action` output.

        :param kwargs: Set up in a way that manageactions.extract_reasons_params
                       can extract the sites for each subtask.
        :returns: View of actions submitted
        :rtype: JSON
        """

        manageactions.fix_sites(**kwargs)
        return self.getaction(1)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def actionshistory(self):
        """
        This API gives the sparse matrix that can be used for training.

        :returns: History of actions on workflows
        :rtype: JSON
        """
        return actionshistorylink.dump_json()

    @cherrypy.expose
    def submitaction(self, workflows='', action='', **kwargs):
        """Submits the action to Unified and notifies the user that this happened

        :param str workflows: is a list of workflows to apply the action to
        :param str action: is the suggested action for Unified to take
        :param kwargs: can include various reasons and additional datasets
        :returns: a confirmation page
        :rtype: str
        """

        cherrypy.log('args: {0}'.format(kwargs))

        if workflows == '':
            return render('scolduser.html', workflow='')

        if action == '':
            return render('scolduser.html', workflow=workflows[0])

        output = ''

        self.seeworkflowlock.acquire()
        try:

            workflows, reasons, params = manageactions.\
                submitaction(cherrypy.request.login, workflows, action, cherrypy.session,
                             **kwargs)

            # Immediately get actions to check the sites list
            check_actions = manageactions.get_actions()
            blank_sites_subtask = []
            sites_to_run = {}
            # Loop through all workflows just submitted
            for workflow in workflows:
                # Check sites of recovered workflows
                if check_actions[workflow]['Action'] in ['acdc', 'recovery']:
                    for subtask, params in check_actions[workflow]['Parameters'].iteritems():
                        # Empty sites are noted
                        if not params.get('sites'):
                            blank_sites_subtask.append('/%s/%s' % (workflow, subtask))
                            sites_to_run['/%s/%s' % (workflow, subtask)] = \
                                globalerrors.check_session(cherrypy.session).\
                                get_workflow(workflow).site_to_run(subtask)

            if blank_sites_subtask:
                drain_statuses = {sitename: drain for sitename, _, drain in \
                                      sitereadiness.i_site_readiness()}
                output = render('picksites.html',
                                tasks=blank_sites_subtask,
                                statuses=drain_statuses,
                                sites_to_run=sites_to_run)

            else:
                output = render('actionsubmitted.html',
                                workflows=workflows,
                                action=action,
                                reasons=reasons,
                                params=params,
                                user=cherrypy.request.login)

        finally:
            self.seeworkflowlock.release()

        return output


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getaction(self, days=0, acted=0):
        """
        The page at ``https://localhost:8080/getaction``
        returns a list of workflows to perform actions on.
        It may be useful to use this page to immediately check
        if your submission went through properly.
        This page will mostly be used by Unified though for acting on operator submissions.

        :param int days: The number of past days to check.
                         The default, 0, means to only check today.
        :param int acted: Used to determine which actions to return.
                          The following values can be used:

                          - 0 - The default value selects actions that have not been run on
                          - 1 - Selects actions reported as submitted by Unified
                          - Negative integer - Selects all actions

        :returns: JSON-formatted information containing actions to act on.
                  The top-level keys of the JSON are the workflow names.
                  Each of these keys refers to a dictionary specifying:

                  - **"Action"** - The action to take on the workflow
                  - **"Reasons"** - A list of reasons for this action
                  - **"Parameters"** - Changes to make for the resubmission
                  - **"user"** - The account name that submitted that action

        :rtype: JSON
        """
        acted = int(acted)
        if acted < 0:
            acted = None
        if acted > 1:
            acted = 1

        return manageactions.get_actions(int(days), acted=acted)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def reportaction(self):
        """
        A POST request to ``https://localhost:8080/reportaction``
        tells the WorkflowWebTools that a set of workflows has been acted on by Unified.
        The body of the POST request must include a JSON with the passphrase
        under ``"key"`` and a list of workflows under ``"workflows"``.

        An example of making this POST request is provided in the file
        ``WorkflowWebTools/test/report_action.py``,
        which relies on ``WorkflowWebTools/test/key.json``.

        :returns: A JSON summarizing results of the request. Keys and values include:

                  - `'valid_key'` - If this is false, the passphrase passed was wrong,
                                    and no action is changed
                  - `'valid_format'` - If false, the input format is unexpected
                  - `'success'` - List of actions that have been marked as acted on
                  - `'already_reported'` - List of workflows that were already removed
                  - `'does_not_exist'` - List of workflows that the database does not know

        :rtype: JSON
        """

        input_json = cherrypy.request.json

        # Is the input good?
        goodkey = (input_json['key'] == serverconfig.config_dict()['actions']['key'])
        goodformat = isinstance(input_json['workflows'], list)

        output = {'valid_key': goodkey, 'valid_format': goodformat}

        if goodkey and goodformat:
            # This output is added to by passing reference to manageactions.report_actions
            manageactions.report_actions(input_json['workflows'], output)

        return output

    @cherrypy.expose
    def explainerror(self, errorcode='0', workflowstep='/'):
        """Returns an explaination of the error code, along with a link returning to table

        :param str errorcode: The error code to display.
        :param str workflowstep: The workflow to return to from the error page.
        :returns: a page dumping the error logs
        :rtype: str
        """

        workflow = workflowstep.split('/')[1]
        if errorcode == '0' or not workflow:
            return 'Need to specify error and workflow. Follow link from workflow tables.'

        errs_explained = globalerrors.check_session(cherrypy.session).\
            get_workflow(workflow).get_explanation(errorcode, workflowstep)

        return render('explainerror.html',
                      error=errorcode,
                      explanation=errs_explained,
                      source=workflowstep)

    @cherrypy.expose
    def newuser(self, email='', username='', password=''):
        """
        New users can register at ``https://localhost:8080/newuser``.
        From this page, users can enter a username, email, and password.
        The username cannot be empty, must contain only alphanumeric characters,
        and must not already exist in the system.
        The email must match the domain names listed on the page or can
        be a specific whitelisted email.
        See :ref:`server-config-ref` for more information on setting valid emails.
        Finally, the password must also be not empty.

        If the registration process is successful, the user will recieve a confirmation
        page instructing them to check their email for a verification link.
        The user account will be activated when that link is followed,
        in order to ensure that the user possesses a valid email.

        The following parameters are sent via POST from the registration page.

        :param str email: The email of the new user
        :param str username: The username of the new user
        :param str password: The password of the new user
        :returns: a page to generate a new user or a confirmation page
        :rtype: str
        :raises: cherrypy.HTTPRedirect back to the new user page without parameters
                 if there was a problem entering the user into the database
        """

        if '' in [email, username, password]:
            return render('newuser.html',
                          emails=serverconfig.get_valid_emails())

        add = manageusers.add_user(email, username, password,
                                   cherrypy.url().split('/newuser')[0])
        if add == 0:
            return render('checkemail.html', email=email)

        raise cherrypy.HTTPRedirect('/newuser')

    @cherrypy.expose
    def confirmuser(self, code):
        """Confirms and activates an account

        :param str code: confirmation code to activate the account
        :returns: confirmation screen for the user
        :rtype: str
        :raises: A redirect the the homepage if the code is invalid
        """

        user = manageusers.confirmation(code)
        if user != '':
            return render('activated.html', user=user)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def resetpassword(self, email='', code='', password=''):
        """
        If a user forgets his or her username or password,
        navigating to ``https://localhost:8080/resetpassword`` will
        allow them to enter their email to reset their password.
        The email will contain the username and a link to reset the password.

        This page is multifunctional, depending on which parameters are sent.
        The link actually redirects to this webpage with a secret code
        that will then allow you to submit a new password.
        The password is then submitted back here via POST.

        :param str email: The email linked to the account
        :param str code: confirmation code to activate the account
        :param str password: the new password for a given code
        :returns: a webview depending on the inputs
        :rtype: str
        :raises: 404 if both email and code are filled
        """

        if not(email or code or password):
            return render('requestreset.html')

        elif not (code or password):
            manageusers.send_reset_email(
                email, cherrypy.url().split('/resetpass')[0])
            return render('sentemail.html', email=email)

        elif not email and code:
            if not password:
                return render('newpassword.html', code=code)

            user = manageusers.resetpassword(code, password)
            return render('resetpassword.html', user=user)

        raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def resetcache(self, prepid='', workflow=''):
        """
        The function is only accessible to someone with a verified account.

        Navigating to ``https://localhost:8080/resetcache``
        resets the error info for the user's session.
        It also clears out cached JSON files on the server.
        Under normal operation, this cache is only refreshed every half hour.

        :returns: a confirmation page
        :rtype: str
        """

        WorkflowTools.RESET_LOCK.acquire()
        cherrypy.log('Cache reset by: %s' % cherrypy.request.login)
        info = globalerrors.check_session(cherrypy.session)

        # Force the cache reset
        if info:
            prepids = [prepid] if prepid else info.prepidinfos.keys()
            workflows = [workflow] if workflow else \
                [wf for pid in prepids for wf in info.prepidinfos[pid].get_workflows()]

            for wkf in workflows:
                info.get_workflow(wkf).get_errors()
                info.get_workflow(wkf).reset()

            if not workflow:
                for pid in prepids:
                    info.prepidinfos[pid].reset()

            info.teardown()
            info.setup()

        WorkflowTools.RESET_LOCK.release()

        return render('complete.html')

    @cherrypy.expose
    def listpage(self, errorcode='', sitename='', workflow=''):
        """
        This returns a list of workflows, site names, or error codes
        that matches the values given for the other two variables.
        The page can be accessed directly by clicking on a corresponding pie chart
        on :ref:`global-view-ref`.

        :param int errorcode: Error to match
        :param str sitename: Site to match
        :param str workflow: The workflow to match
        :returns: Page listing workflows, site names or errors codes
        :rtype: str
        :raises: cherrypy.HTTPRedirect to 404 if all variables are filled
        """

        if errorcode and sitename and workflow:
            raise cherrypy.HTTPError(404)

        acted = [] if workflow else \
            manageactions.get_acted_workflows(
                serverconfig.get_history_length())

        # Retry after ProgrammingError
        try:
            info = listpage.listworkflows(errorcode, sitename, workflow, cherrypy.session)
        except sqlite3.ProgrammingError:
            time.sleep(5)
            return self.listpage(errorcode, sitename, workflow)

        return render('listworkflows.html',
                      workflow=workflow,
                      errorcode=errorcode,
                      sitename=sitename,
                      acted_workflows=acted,
                      info=info)
