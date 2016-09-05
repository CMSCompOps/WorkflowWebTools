#!/usr/bin/env python2.7

"""
.. describe:: workflowtools.py

Script to by run the WorkflowWebTools server.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os

import cherrypy
from mako.lookup import TemplateLookup

from WorkflowWebTools import showlog
from WorkflowWebTools import serverconfig
from WorkflowWebTools import globalerrors
from WorkflowWebTools import manageusers
from WorkflowWebTools import manageactions
from WorkflowWebTools import clusterworkflows


GET_TEMPLATE = TemplateLookup(directories=['templates'],
                              module_directory='templates/mako_modules').get_template
"""Function to get templates from the relative ``templates`` directory"""


class WorkflowTools(object):
    """This class holds all of the exposed methods for the Workflow Webpage"""

    def __init__(self):
        """Initializes the service by creating clusters"""
        self.cluster()

    @cherrypy.expose
    def index(self):
        """
        :returns: The welcome page
        :rtype: str
        """
        return GET_TEMPLATE('welcome.html').render()

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
        self.clusterer = clusterworkflows.get_clusterer(
            serverconfig.workflow_history_path())
        return GET_TEMPLATE('complete.html').render()

    @cherrypy.expose
    def showlog(self, search=''):
        """
        This page, located at ``https://localhost:8080/showlog``,
        returns logs that are stored in an elastic search server.
        More details can be found at :ref:`elastic-search-ref`.
        If directed here from :ref:`workflow-view-ref`, then
        the search will be for the relevant workflow.

        :param str search: The search string
        :returns: the logs from elastic search
        :rtype: str
        """
        logdata = showlog.give_logs(search)
        if isinstance(logdata, dict):
            return GET_TEMPLATE('showlog.html').render(logdata=logdata)
        else:
            return logdata

    @cherrypy.expose
    def globalerror(self, pievar='errorcode'):
        """
        This page, located at ``https://localhost:8080/globalerror``,
        attempts to give an overall view of the errors that occurred
        in each workflow at different sites.
        The resulting view is a tabel of piecharts.
        The rows and columns can be adjusted to contain two of the following:

        - Workflow step name
        - Site where error occurred
        - Exit code of the error

        The third variable is used to split the pie charts.
        This variable can be quickly changed by submitting the form in the
        upper left corner of the page.
        The piecharts' size depend on the total number of errors in a given cell.

        Each cell also has a tooltip, containing more information.
        The piecharts show the exact splitting based on the extra variable.
        Error codes in the columns give a tooltip with part of their error message
        from multiple jobs appended.

        If the steps make up the rows, you can follow the link of the step name to view
        the :ref:`workflow-view-ref`.
        Following that link will also cause your browser to jump to the corresponding
        step table on that page.

        :param str pievar: The variable that the pie charts are split into.
                           Valid values are:

                           - errorcode
                           - sitename
                           - stepname

        :returns: the global views of errors
        :rtype: str
        """

        return GET_TEMPLATE('globalerror.html').\
            render(errordata=globalerrors.return_page(pievar, cherrypy.session),
                   acted_workflows=manageactions.get_acted_workflows(
                       serverconfig.get_history_length()))

    @cherrypy.expose
    def seeworkflow(self, workflow='', issuggested=''):
        """
        Located at ``https://localhost:8080/seeworkflow``,
        this shows detailed tables of errors for each step in a workflow.

        For the exit codes in each row, there is a link to view some of the output
        of the error message for jobs having the given exit code.
        This should help operators understand what the error means.

        At the top of the page, there are links back for :ref:`global-view-ref`
        and :ref:`show-logs-ref`.
        There is also a form to submit actions.
        Note that you will need to register in order to actually submit actions.
        See :ref:`new-user-ref` for more details.
        Depending on which action is selected, a menu will appear below to
        pick how to adjust parameters for the workflows.

        .. todo::
          Document the different actions and parameters.
          Try to centralize this list in some nice way.

        Under the selection of the action and parameters, there is a button
        to show other workflows that are similar to the selected workflow,
        if there are other workflows in the same cluster.
        There will be a link to open a similar workflow view page in a new tab.
        The option to submit actions will not be on this page though
        (so that you can focus on the first workflow).
        If you think that a workflow in the cluster should have the same actions
        applied to it as the parent workflow,
        then check the box next to the workflow name.
        Any action submitted will be applied to all checked workflows,
        in addition to the workflow on the page where the action is submitted from.

        Finally, before submitting, you can submit reasons for your action selection.
        Clicking the Add Reason button will give you an additional reason field.
        Reasons submitted are stored based on the short reason you give.
        You can then select past reasons from the drop down menu in the future,
        to save some time.
        If you do not want to store your reason, do not fill in the Short Reason field.
        The long reason will be used automatically for logging reasons.

        :param str workflow: is the name of the workflow to look at
        :param str issuggested: is a string to tell if the page
                                has been linked from another workflow page
        :returns: the error tables page for a given workflow
        :rtype: str
        :raises: cherrypy.HTTPRedirect to :ref:`global-view-ref` if a workflow
                 is not selected.
        """

        if workflow == '':
            raise cherrypy.HTTPRedirect('/globalerror')

        if issuggested:
            similar_wfs = []
        else:
            similar_wfs = clusterworkflows.\
                get_clustered_group(workflow, self.clusterer, cherrypy.session)

        return GET_TEMPLATE('workflowtables.html').\
            render(workflowdata=globalerrors.see_workflow(workflow, cherrypy.session),
                   workflow=workflow, issuggested=issuggested,
                   similar_wfs=similar_wfs
                  )

    @cherrypy.expose
    def submitaction(self, workflows='', action='', **kwargs):
        """Submits the action to Unified and notifies the user that this happened

        :param str workflows: is a list of workflows to apply the action to
        :param str action: is the suggested action for Unified to take
        :param kwargs: can include various reasons and additional datasets
        :returns: a confirmation page
        :rtype: str
        """

        if workflows == '':
            return GET_TEMPLATE('scolduser.html').render(workflow='')

        if action == '':
            return GET_TEMPLATE('scolduser.html').render(workflow=workflows[0])

        workflows, action, reasons, params = manageactions.\
            submitaction(cherrypy.request.login, workflows, action, **kwargs)

        return GET_TEMPLATE('actionsubmitted.html').\
            render(workflows=workflows, action=action,
                   reasons=reasons, params=params, user=cherrypy.request.login)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getaction(self, days=0, test=False):
        """Returns the latest action json that has not been adressed yet.

        :param int days: The number of past days to check.
                         The default, 0, means to only check today.
        :param bool test: Used to determine whether or not to return the test file.
        :returns: a JSON file containing actions to act on
        :rtype: JSON
        """

        # This will also need to somehow note that an action has been gotten by Unified

        if test:
            return {
                'test' : {
                    'Actions': 'test',
                    'Parameters': {
                        'test': 'True',
                        'what': 'test'
                        },
                    'Reasons': 'I needed a test'
                    }
                }

        return manageactions.get_actions(days)

    @cherrypy.expose
    def explainerror(self, errorcode="0", workflowstep="/"):
        """Returns an explaination of the error code, along with a link returning to table

        :param str errorcode: The error code to display.
        :param str workflowstep: The workflow to return to from the error page.
        :returns: a page dumping the error logs
        :rtype: str
        """

        if errorcode == "0":
            return 'Need to specify error. Follow link from workflow tables.'

        return GET_TEMPLATE('explainerror.html').\
            render(error=errorcode,
                   explanation=globalerrors.check_session(cherrypy.session).\
                       get_errors_explained().\
                       get(errorcode, ['No info for this error code']),
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
            return GET_TEMPLATE('newuser.html').\
                render(emails=serverconfig.get_valid_emails())

        add = manageusers.add_user(email, username, password,
                                   cherrypy.url().split('/newuser')[0])
        if add == 0:
            return GET_TEMPLATE('checkemail.html').render(email=email)
        else:
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
            return GET_TEMPLATE('activated.html').render(user=user)
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
            return GET_TEMPLATE('requestreset.html').render()

        elif not (code or password):
            manageusers.send_reset_email(
                email, cherrypy.url().split('/resetpass')[0])
            return GET_TEMPLATE('sentemail.html').render(email=email)

        elif not email and code:
            if not password:
                return GET_TEMPLATE('newpassword.html').render(code=code)
            else:
                user = manageusers.resetpassword(code, password)
                return GET_TEMPLATE('resetpassword.html').render(user=user)
        else:
            raise cherrypy.HTTPError(404)

    @cherrypy.expose
    def resetcache(self):
        """
        The function is only accessible to someone with a verified account.

        Navigating to ``https://localhost:8080/resetcache``
        resets the error info for the user's session.
        Under normal operation, this cache is only refreshed every half hour.

        :returns: a confirmation page
        :rtype: str
        """
        if cherrypy.session.get('info'):
            cherrypy.session.get('info').teardown()
            cherrypy.session.get('info').setup()
        return GET_TEMPLATE('complete.html').render()

def secureheaders():
    """Generates secure headers for cherrypy Tool"""
    headers = cherrypy.response.headers
    headers['Strict-Transport-Security'] = 'max-age=31536000'
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"


if __name__ == '__main__':
    CONF = {
        'global': {
            'server.socket_host': serverconfig.host_name(),
            'server.socket_port': serverconfig.host_port()
            },
        '/': {
            'error_page.401': GET_TEMPLATE('401.html').render,
            'error_page.404': GET_TEMPLATE('404.html').render,
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.sessions.on': True,
            'tools.sessions.secure': True,
            'tools.sessions.httponly': True,
            },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
            },
        '/submitaction': {
            'tools.auth_basic.on': True,
            'tools.auth_basic.realm': 'localhost',
            'tools.auth_basic.checkpassword': manageusers.validate_password
            }
        }
    for key in ['/cluster', '/resetcache']:
        CONF[key] = CONF['/submitaction']

    if os.path.exists('keys/cert.pem') and os.path.exists('keys/privkey.pem'):
        cherrypy.tools.secureheaders = \
            cherrypy.Tool('before_finalize', secureheaders, priority=60)
        cherrypy.config.update({
            'server.ssl_certificate': 'keys/cert.pem',
            'server.ssl_private_key': 'keys/privkey.pem'
            })

    cherrypy.quickstart(WorkflowTools(), '/', CONF)
