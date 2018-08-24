"""Module for manipulating the database that stores past operator reasons.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import sqlite3
import cherrypy

from . import serverconfig

DEFAULT_SHORT = '---- No Short Reason Given, Not Saved to Database! ----'


def get_reasons():
    """Gets the reasons database in the local directory.

    :returns: the reasons connection, cursor
    :rtype: (sqlite3.Connection, sqlite3.Cursor)
    """

    conn = sqlite3.connect(os.path.join(serverconfig.config_dict()['workspace'], 'reasons.db'))
    curs = conn.cursor()
    curs.execute('SELECT name FROM sqlite_master WHERE type="table" and name="reasons"')

    if not curs.fetchone():
        curs.execute('CREATE TABLE reasons (shortreason varchar(255) PRIMARY KEY, '
                     'longreason varchar(4095))')

    return conn, curs


def update_reasons(reasons):
    """Gets the reasons for a given action and updates the reasons db

    :param reasons: is a list of dictionaries of short and long reasons,
                    with keys 'short' and 'long'
    :type reasons: list of dicts
    :raises TypeError: if the parameter is not a list
    :raises KeyError: if the dictionaries in the list do not have the correct structure
    """

    conn, curs = get_reasons()

    if not isinstance(reasons, list):
        raise TypeError('reasons is not a list')

    try:
        for reason in reasons:
            if reason['short'] == DEFAULT_SHORT:
                continue
            curs.execute('SELECT shortreason FROM reasons WHERE shortreason=?', (reason['short'],))
            if not curs.fetchone():
                curs.execute('INSERT INTO reasons VALUES (?,?)', (reason['short'], reason['long'],))
        conn.commit()
    except KeyError:
        cherrypy.log('Parameter does not have correct keys.')
        raise

    conn.close()


def short_reasons_list():
    """Get the list of short reasons

    :returns: the list of short reasons
    :rtype: list of strs
    """

    conn, curs = get_reasons()

    curs.execute('SELECT shortreason FROM reasons')
    short_list = []
    for item, in curs.fetchall():
        short_list.append(item)

    conn.close()

    return short_list


def reasons_list():
    """Get the full list of reasons

    :returns: all of the reasons in a dictionary with the short reasons being the key
    :rtype: dict
    """

    short_list = short_reasons_list()

    conn, curs = get_reasons()

    reasons = {}

    for short in short_list:
        curs.execute('SELECT longreason FROM reasons WHERE shortreason=?', (short,))
        longreason = ''
        for item in curs.fetchall():
            longreason += (item[0])

        reasons[short] = longreason

    conn.close()

    return reasons
