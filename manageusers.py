"""
Module to manage users of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import sqlite3

from CMSToolBox.emailtools import send_email


def get_user_db():
    """Gets the users database in the local directory.

    :returns: the users connection, cursor
    :rtype: (sqlite3.Connection, sqlite3.Cursor)
    """

    conn = sqlite3.connect('users.db')
    curs = conn.cursor()
    curs.execute('SELECT name FROM sqlite_master WHERE type="table" and name="users"')

    if not curs.fetchone():
        # Note that the only un-encrypted value will be the username
        # Email is kept for password reset of a user
        curs.execute('CREATE TABLE users (username varchar(31) PRIMARY KEY, email varchar(255) UNIQUE, '
                     'password varchar(1023), validator varchar(1023), isvalid integer)')

    return conn, curs


def add_user(email, username, password):
    """Adds the user to the users database and sends a verification email, 
       if the parameters are valid.

    :param str email: The user email to send verification to.
                      Make sure to check for valid domains.
    :param str username: The username of the account to add.
    :param str password: The password to be stored.
    """

    # Need to check parameters again so that some sneaky guy doesn't pass the javascript
    if ((email.endswith('@cern.ch') or email.endswith('@fnal.gov')) 
        and len(username) != 0 and len(password) != 0):

        conn, curs = get_user_db()

        conn.close()
