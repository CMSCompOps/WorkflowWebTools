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

from WorkflowWebTools import *

templates = TemplateLookup(directories=['templates'], module_directory='templates/mako_modules')
get_template = templates.get_template


class WorkflowTools(object):
    """This class holds all of the exposed methods for the Workflow Webpage"""

    @cherrypy.expose
    def index(self):
        """Returns the index page"""
        return get_template('welcome.html').render()

    @cherrypy.expose
    def showlog(self, search=''):
        """Returns the logs from elastic search"""
        logdata = showlog.give_logs(search)
        if type(logdata) == dict:
            return get_template('showlog.html').render(logdata=logdata)
        else:
            return logdata

    @cherrypy.expose
    def globalerror(self, pievar='errorcode'):
        """Shows the global views of errors"""
        # This can use a lot of reworking
        return get_template('globalerror.html').render(errordata=globalerrors.return_page(pievar, cherrypy.session))

    @cherrypy.expose
    def seeworkflow(self, workflow='', issuggested=''):
        """Shows the errors for a given workflow

        :param workflow: is the name of the workflow to look at
        :param issuggested: is a string to tell if the page has been linked from another workflow page
        """
        # This can use a lot of reworking
        if workflow == '':
            return 'Did not select a workflow! <br> \
                    You can do that from the <a href="../globalerror">Global Errors Page</a>'

        return get_template('workflowtables.html').render(
            workflowdata=globalerrors.see_workflow(workflow, cherrypy.session),
                                                   workflow=workflow, issuggested=issuggested)

    @cherrypy.expose
    def submitaction(self, workflow='', action='', **kwargs):
        """Submits the action to Unified and notifies the user that this happened
        
        :param workflow: is the original workflow name
        :param action: is the suggested action for Unified to take
        :param kwargs: can include various reasons and additional datasets
        """

        if action == '':
            return get_template('scolduser.html').render(workflow=workflow)

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
                'Reasons': [reason['long'] for reason in (reasons + notupdate)]
                }

        with open(output_file_name, 'w') as outputfile:
            json.dump(add_to_json, outputfile)

        return get_template('actionsubmitted.html').render(workflows=workflows, 
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


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            'tools.sessions.on': True,
            'tools.sessions.timeout': 5,
            'tools.sessions.cleanup_freq': 5,
            },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static'
            },
        '/actions': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './actions'
            }
        }

    # Set the host of the webpage
    this_host = socket.gethostname().split('.')[0]

    # If on vocms machine, serve there, otherwise just show page on localhost:8080
    if 'vocms' in this_host:
        cherrypy.config.update({'server.socket_host': this_host + '.cern.ch',
                                'server.socket_port': 80,
                                })

    cherrypy.quickstart(WorkflowTools(), '/', conf)
