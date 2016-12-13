"""Simple utils functions that do not rely on a session.

These are separated from globalerrors, since we do not need
to generate an ErrorInfo instance in other applications.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import os
import json
import urllib2
import re
import validators
import cherrypy

from CMSToolBox import workflowinfo


def open_location(data_location):
    """
    Opens the data location and returns the file handle.

    :param str data_location: The location of the file or url
    :returns: the file handle for the data or None if failed
    :rtype: file
    """
    if os.path.isfile(data_location):
        return open(data_location, 'r')

    else:
        if validators.url(data_location):
            try:
                return urllib2.urlopen(data_location)
            except urllib2.URLError as msg:
                cherrypy.log(msg, 'while trying to open', data_location)

    return None


def add_to_database(curs, data_location):
    """Add data from a file to a central database through the passed cursor

    :param sqlite3.Cursor curs: is the cursor to the database
    :param data_location: If a string, this
         is the location of the file
         or url of data to add to the database.
         This should be in JSON format, and if a local file does not exist,
         a url will be assumed. If the url is invalid,
         an empty database will be returned.
         If a list, it's a list of status to get workflows from wmstats.
    :type data_location: str or list
    """
    if isinstance(data_location, list):
        indict = {}
        for status in data_location:
            cherrypy.log('Getting status %s' % status)
            for workflow in workflowinfo.list_workflows(status):
                cherrypy.log('Getting workflow %s' % workflow)
                indict.update(workflowinfo.errors_for_workflow(workflow))

    else:
        res = open_location(data_location)

        if not res:
            return

        indict = json.load(res)
        res.close()

    for stepname, errorcodes in indict.items():
        for errorcode, sitenames in errorcodes.items():
            if not re.match(r'\d+', errorcode):
                continue

            for sitename, numbererrors in sitenames.items():
                full_key = '_'.join([stepname, sitename, errorcode])
                if not curs.execute(
                        'SELECT EXISTS(SELECT 1 FROM workflows WHERE fullkey=? LIMIT 1)',
                        (full_key,)).fetchone()[0]:
                    curs.execute('INSERT INTO workflows VALUES (?,?,?,?,?)',
                                 (full_key, stepname, errorcode,
                                  sitename, numbererrors))


def create_table(curs):
    """Create the workflows error table with the proper format
    :param sqlite3.Cursor curs: is the cursor to the database
    """

    curs.execute(
        'CREATE TABLE workflows (fullkey varchar(1023) UNIQUE, '
        'stepname varchar(255), errorcode int, '
        'sitename varchar(255), numbererrors int)')
