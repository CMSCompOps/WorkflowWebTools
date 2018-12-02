"""Simple utils functions that do not rely on a session.

These are separated from globalerrors, since we do not need
to generate an ErrorInfo instance in other applications.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


import os
import json
import re
import urlparse

import validators
import cherrypy
import cx_Oracle

from cmstoolbox import sitereadiness
from cmstoolbox.webtools import get_json

from . import workflowinfo
from . import serverconfig

def errors_from_list(workflows):
    """
    :param list workflows: A list of workflows that are in assistance-manual
    :returns: The errors for the workflows
    :rtype: dict
    """
    indict = {}

    for workflow in workflows:
        base = workflowinfo.WorkflowInfo(workflow)
        prep_id = base.get_prep_id()
        for wkf in set(workflowinfo.PrepIDInfo(prep_id).get_workflows()):
            indict.update(
                workflowinfo.WorkflowInfo(wkf).get_errors(get_unreported=True)
                )

    return indict


def open_location(data_location):
    """
    This function assumes that the contents of the location is in JSON format.
    It opens the data location and returns the dictionary.

    :param str data_location: The location of the file or url
    :returns: information in the JSON file
    :rtype: dict
    """
    config_dict = serverconfig.config_dict()

    if 'oracle' in config_dict:
        oracle_db_conn = cx_Oracle.connect(*config_dict['oracle']) # pylint:disable=c-extension-no-member
        oracle_cursor = oracle_db_conn.cursor()
        oracle_cursor.execute(
            "SELECT NAME FROM CMS_UNIFIED_ADMIN.workflow WHERE lower(STATUS) LIKE '%manual%'")
        wkfs = [row for row, in oracle_cursor]
        oracle_db_conn.close()
        cherrypy.log('Number of workflows from database: %i' % len(wkfs))
        return errors_from_list(wkfs)

    raw = None

    if os.path.isfile(data_location):
        with open(data_location, 'r') as input_file:
            raw = json.load(input_file)

    elif validators.url(data_location):
        components = urlparse.urlparse(data_location)

        # Anything we need for the Shibboleth cookie could be in the config file
        cookie_stuff = config_dict['data']

        raw = get_json(components.netloc, components.path,
                       use_https=True,
                       cookie_file=cookie_stuff.get('cookie_file'),
                       cookie_pem=cookie_stuff.get('cookie_pem'),
                       cookie_key=cookie_stuff.get('cookie_key'))

    if raw is None:
        return raw

    keys = raw.keys()
    if not (keys and isinstance(raw[keys[0]], list)):
        return raw

    return errors_from_list([
        workflow for workflow, statuses in raw.iteritems()
        if True in ['manual' in status for status in statuses]
    ])


def get_list_info(status_list):
    """
    Get the list of workflows that match the statuses listed
    via :py:mod:`workflowinfo`.

    :param list status_list: The list of workflow statuses to get the info for
    :returns: The workflow info dictionary, which matches the format of
              the unified all_errors.json.
    :rtype: dict
    """

    indict = {}
    for workflow in status_list:
        indict.update(
            workflowinfo.WorkflowInfo(workflow).get_errors(get_unreported=True)
            )

    return indict


def add_to_database(curs, data_location): # pylint: disable=too-complex
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

    indict = get_list_info(data_location) \
        if isinstance(data_location, list) else \
        (open_location(data_location) or {})

    number_added = 0

    for stepname, errorcodes in indict.items():
        if 'LogCollect' in stepname or 'Cleanup' in stepname:
            continue

        for errorcode, sitenames in errorcodes.items():
            if errorcode == 'NotReported':
                errorcode = '-1'

            elif not re.match(r'\d+', errorcode):
                continue

            for sitename, numbererrors in sitenames.items():
                numbererrors = numbererrors or int(errorcode == '-1')

                if numbererrors:
                    full_key = '_'.join([stepname, sitename, errorcode])
                    if not list(curs.execute(
                            'SELECT EXISTS(SELECT 1 FROM workflows WHERE fullkey=? LIMIT 1)',
                            (full_key,)))[0][0]:
                        number_added += 1
                        curs.execute('INSERT INTO workflows VALUES (?,?,?,?,?,?)',
                                     (full_key, stepname, errorcode,
                                      sitename, numbererrors,
                                      sitereadiness.site_readiness(sitename)))

    # This is to prevent the ErrorInfo objects from locking the database
    if 'conn' in dir(curs):
        curs.conn.commit()

    if number_added:
        cherrypy.log('Number of points added to the database: %i' % number_added)


def create_table(curs):
    """Create the workflows error table with the proper format
    :param sqlite3.Cursor curs: is the cursor to the database
    """

    curs.execute(
        'CREATE TABLE workflows (fullkey varchar(1023) UNIQUE, '
        'stepname varchar(255), errorcode int, '
        'sitename varchar(255), numbererrors int, '
        'sitereadiness varchar(15))')
    # Hopefully this makes lookups faster
    curs.execute('CREATE INDEX composite_index ON workflows (stepname, errorcode, sitename)')
