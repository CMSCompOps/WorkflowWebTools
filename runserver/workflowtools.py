#!/usr/bin/env python

"""
Script to by run by a Python instance with cherrypy and mako installed

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import glob

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
        """Initializes the service."""
        confirm = self.cluster()

    @cherrypy.expose
    def index(self):
        """
        :returns: The welcome page
        :rtype: str
        """
        return GET_TEMPLATE('welcome.html').render()

    @cherrypy.expose
    def cluster(self):
        """Does the clustering for this instance"""
        self.clusterer = clusterworkflows.get_clusterer(
            serverconfig.workflow_history_path())
        return 'Done!'

    @cherrypy.expose
    def showlog(self, search=''):
        """Generates the :ref:`show-ref` page.

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
        """Generates the :ref:`global-view-ref` page.

        :param str pievar: The variable that the pie charts are split into.
                           Valid values are:
                           - errorcode
                           - sitename
                           - stepname
        :returns: the global views of errors
        :rtype: str
        """

        return GET_TEMPLATE('globalerror.html').\
            render(errordata=globalerrors.return_page(pievar, cherrypy.session))

    @cherrypy.expose
    def seeworkflow(self, workflow='', issuggested=''):
        """Shows the errors for a given workflow

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

        if action == '':
            return GET_TEMPLATE('scolduser.html').render(workflow=workflows[0])

        workflows, action, reasons, params = manageactions.\
            submitaction(cherrypy.request.login, workflows, action, **kwargs)

        return GET_TEMPLATE('actionsubmitted.html').\
            render(workflows=workflows, action=action,
                   reasons=reasons, params=params, user=cherrypy.request.login)

    @cherrypy.expose
    def getaction(self, test=False):
        """Returns the latest action json that has not been adressed yet.

        :param bool test: Used to determine whether or not to return the test file.
        :raises: A redirect to the relevant JSON.
        """

        # This will also need to somehow note that an action has been gotten by Unified

        if test:
            raise cherrypy.HTTPRedirect('/actions/test.json')

        newest_json = max(glob.iglob('actions/*.json'), key=os.path.getmtime)
        raise cherrypy.HTTPRedirect('/' + newest_json)

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
        """The page for registering a new user.

        If accessing the page without filling one of the parameters,
        you will get a form to submit back to this page via POST.
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
        """

        user = manageusers.confirmation(code)
        if user != '':
            return GET_TEMPLATE('activated.html').render(user=user)
        return self.index()

    @cherrypy.expose
    def resetpassword(self, email='', code='', password=''):
        """Resets the password for a user.

        Accessing with no parameters allows you to submit an email for
        password reset. Submitting an email sends a reset code.
        Submitting with a code allows you to reset the password.
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
            'error_page.401': 'templates/401.html',
            'error_page.404': 'templates/404.html',
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.sessions.on': True,
            'tools.sessions.secure': True,
            'tools.sessions.httponly': True,
            },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
            },
        '/actions': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './actions'
            },
        '/submitaction': {
            'tools.auth_basic.on': True,
            'tools.auth_basic.realm': 'localhost',
            'tools.auth_basic.checkpassword': manageusers.validate_password
            }
        }

    if os.path.exists('keys/cert.pem') and os.path.exists('keys/privkey.pem'):
        cherrypy.tools.secureheaders = \
            cherrypy.Tool('before_finalize', secureheaders, priority=60)
        cherrypy.config.update({
            'server.ssl_certificate': 'keys/cert.pem',
            'server.ssl_private_key': 'keys/privkey.pem'
            })

    cherrypy.quickstart(WorkflowTools(), '/', CONF)
