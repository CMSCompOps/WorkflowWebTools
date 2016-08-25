#!/usr/bin/env python

"""
Script to by run by a Python instance with cherrypy and mako installed

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import glob
import socket
import json

import cherrypy
from mako.lookup import TemplateLookup

from WorkflowWebTools import showlog
from WorkflowWebTools import globalerrors
from WorkflowWebTools import reasonsmanip
from WorkflowWebTools import manageusers


GET_TEMPLATE = TemplateLookup(directories=['templates'],
                              module_directory='templates/mako_modules').get_template


def validate_password(_, username, password):

    if username == 'test' and password == 'test':
        return True
    return False


class WorkflowTools(object):
    """This class holds all of the exposed methods for the Workflow Webpage"""

    @cherrypy.expose
    def index(self):
        """Returns the index page"""
        return GET_TEMPLATE('welcome.html').render()

    @cherrypy.expose
    def showlog(self, search=''):
        """Returns the logs from elastic search"""
        logdata = showlog.give_logs(search)
        if type(logdata) == dict:
            return GET_TEMPLATE('showlog.html').render(logdata=logdata)
        else:
            return logdata

    @cherrypy.expose
    def globalerror(self, pievar='errorcode'):
        """Shows the global views of errors"""
        # This can use a lot of reworking
        return GET_TEMPLATE('globalerror.html').\
            render(errordata=globalerrors.return_page(pievar, cherrypy.session))

    @cherrypy.expose
    def seeworkflow(self, workflow='', issuggested=''):
        """Shows the errors for a given workflow

        :param workflow: is the name of the workflow to look at
        :param issuggested: is a string to tell if the page
                            has been linked from another workflow page
        """
        # This can use a lot of reworking
        if workflow == '':
            return 'Did not select a workflow! <br> \
                    You can do that from the <a href="../globalerror">Global Errors Page</a>'

        return GET_TEMPLATE('workflowtables.html').\
            render(workflowdata=globalerrors.see_workflow(workflow, cherrypy.session),
                   workflow=workflow, issuggested=issuggested)

    @cherrypy.expose
    def submitaction(self, workflow='', action='', **kwargs):
        """Submits the action to Unified and notifies the user that this happened

        :param workflow: is the original workflow name
        :param action: is the suggested action for Unified to take
        :param kwargs: can include various reasons and additional datasets
        """

        if action == '':
            return GET_TEMPLATE('scolduser.html').render(workflow=workflow)

        workflows = [workflow]
        old_reasons = reasonsmanip.reasons_list()

        reasons = []
        notupdate = []
        params = {}

        for key, item in kwargs.iteritems():

            if 'shortreason' in key:
                long = kwargs[key.replace('short', 'long')].strip().replace('\n', '<br>')

                if len(long) == 0:
                    continue

                if item != '':
                    reasons.append({
                        'short': item,
                        'long': long,
                    })
                else:
                    notupdate.append({
                        'short': '---- No Short Reason Given, Not Saved to Database! ----',
                        'long': long,
                    })

            elif 'selectedreason' in key:

                if type(item) is list:

                    for short in item:

                        if short == "none":
                            continue
                        notupdate.append({
                            'short': short,
                            'long': old_reasons[short],
                        })

                else:
                    if item == "none":
                        continue
                    notupdate.append({
                        'short': item,
                        'long': old_reasons[item],
                    })

            elif 'param_' in key:
                parameter = '_'.join(key.split('_')[1:])
                params[parameter] = item

        reasonsmanip.update_reasons(reasons)

        output_file_name = 'actions/new_action.json'

        add_to_json = {}
        if os.path.isfile(output_file_name):
            with open(output_file_name, 'r') as outputfile:
                add_to_json = json.load(outputfile)

        for wf in workflows:
            add_to_json[wf] = {
                'Action': action,
                'Parameters': params,
                'Reasons': [reason['long'] for reason in reasons + notupdate]
                }

        with open(output_file_name, 'w') as outputfile:
            json.dump(add_to_json, outputfile)

        return GET_TEMPLATE('actionsubmitted.html').render(workflows=workflows,
                                                           action=action,
                                                           reasons=(reasons+notupdate),
                                                           params=params)

    @cherrypy.expose
    def getaction(self, test=False):
        """Returns the latest action json that has not been adressed yet."""

        # This will also need to somehow note that an action has been gotten by Unified

        if test:
            raise cherrypy.HTTPRedirect('/actions/test.json')

        newest_json = max(glob.iglob('actions/*.json'), key=os.path.getmtime)
        raise cherrypy.HTTPRedirect('/' + newest_json)

    @cherrypy.expose
    def explainerror(self, errorcode="0", workflowstep="/"):
        """Returns an explaination of the error code, along with a link returning to table"""

        if errorcode == "0":
            return 'Need to specify error. Follow link from workflow tables.'

        return GET_TEMPLATE('explainerror.html').\
            render(error=errorcode,
                   explanation=globalerrors.check_session(cherrypy.session).\
                       get_errors_explained().\
                       get(errorcode, ['No info for this error code']),
                   source=workflowstep)

    @cherrypy.expose
    def newuser(self):
        """Returns a page to generate a new user"""
        return GET_TEMPLATE('newuser.html').render()

    @cherrypy.expose
    def registeruser(self, email, username, password):
        """Returns a page to generate a new user"""
        manageusers.add_user(email, username, password)
        return GET_TEMPLATE('newuser.html').render()


def secureheaders():
    headers = cherrypy.response.headers
    headers['Strict-Transport-Security'] = 'max-age=31536000'
    headers['X-Frame-Options'] = 'DENY'
    headers['X-XSS-Protection'] = '1; mode=block'
    headers['Content-Security-Policy'] = "default-src='self'"


if __name__ == '__main__':
    conf = {
        '/': {
            'error_page.401': 'templates/401.html',
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.sessions.on': True,
            'tools.sessions.secure': True,
            'tools.sessions.httponly': True
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
            'tools.auth_basic.checkpassword': validate_password
            }
        }

    # Set the host of the webpage
    this_host = socket.gethostname().split('.')[0]

    # If on vocms machine, serve there, otherwise just show page on localhost:8080
    if 'vocms' in this_host:
        cherrypy.config.update({'server.socket_host': this_host + '.cern.ch',
                                'server.socket_port': 80,
                               })

    if os.path.exists('keys/cert.pem') and os.path.exists('keys/privkey.pem'):
        cherrypy.tools.secureheaders = \
            cherrypy.Tool('before_finalize', secureheaders, priority=60)
        cherrypy.config.update({
            'server.ssl_certificate': 'keys/cert.pem',
            'server.ssl_private_key': 'keys/privkey.pem'
            })

    # Refuse to open if the salt.txt file is not there.
    with open('keys/salt.txt', 'r') as saltfile:
        if len(saltfile.readlines()) == 0:
            exit(1)

    cherrypy.quickstart(WorkflowTools(), '/', conf)
