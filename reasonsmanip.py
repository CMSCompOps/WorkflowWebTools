"""Module for manipulating the database that stores past operator reasons.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import sqlite3

from .serverconfig import LOCATION


def get_reasons():
    """Gets the reasons database in the local directory.

    :returns: the reasons connection, cursor
    :rtype: (sqlite3.Connection, sqlite3.Cursor)
    """

    conn = sqlite3.connect(os.path.join(LOCATION, 'reasons.db'))
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
    """

    conn, curs = get_reasons()

    for reason in reasons:
        curs.execute('SELECT shortreason FROM reasons WHERE shortreason=?', (reason['short'],))
        if not curs.fetchone():
            curs.execute('INSERT INTO reasons VALUES (?,?)', (reason['short'], reason['long'],))

    conn.commit()
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

    :returns: all of the reaons in a dictionary
    :rtype: list of dicts
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
