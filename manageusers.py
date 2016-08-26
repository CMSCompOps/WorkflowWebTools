"""
Module to manage users of WorkflowWebTools.

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import sqlite3
import random
import uuid
import urllib
import re

from passlib.hash import bcrypt
from CMSToolBox.emailtools import send_email


def get_user_db():
    """Gets the users database in the local directory.

    :returns: the users connection, cursor
    :rtype: sqlite3.Connection, sqlite3.Cursor
    """

    conn = sqlite3.connect('users.db')
    curs = conn.cursor()
    curs.execute('SELECT name FROM sqlite_master WHERE type="table" and name="users"')

    if not curs.fetchone():
        # Note that the only un-encrypted value will be the username
        # Email is kept (but hashed and salted) for password reset of a user
        curs.execute('CREATE TABLE users (username varchar(31) PRIMARY KEY, '
                     'email varchar(255) UNIQUE, password varchar(1023), '
                     'validator varchar(1023), isvalid integer)')

    return conn, curs


def validate_password(_, username, password):
    """Verifies users' logon attempts.
    This is called automatically by cherrypy,
    hence the unused parameter.

    :param str _: The hostname
    :param str username: The attempted username
    :param str password: The attempted password
    :returns: Whether or not the loging attempt succeeds
    :rtype: bool
    """

    conn, curs = get_user_db()

    curs.execute('SELECT password FROM users WHERE username=?',
                 (username,))

    passwords = list(curs.fetchall())
    conn.close()

    if len(passwords) != 1:
        return False

    if do_salt_hash(password) == passwords[0][0]:
        return True
    return False


def confirmation(code, lookup='validator', return_curs=False):
    """Determine the user from the confirmation code and activate the account

    :param str code: the confirmation code for the user
    :param str lookup: The field to look up the username with
    :param bool return_curs: If false, closes the connection
    :returns: the user name if valid code, or '' if not.
              Followed by conn, curs if return_curs is True
    :rtype: str [, sqlite3.Connection, sqlite3.Cursor]
    """

    check_code = do_salt_hash(code)
    conn, curs = get_user_db()
    curs.execute('SELECT username FROM users WHERE ?=?', (lookup, check_code))

    users = list(curs.fetchall())

    if len(users) != 1:
        conn.close()
        return ''

    user = users[0][0]

    if lookup == 'validator':
        curs.execute('UPDATE users SET validator=?, isvalid=? WHERE username=?',
                     ('0', 1, user))
        conn.commit()

    if return_curs:
        return user, conn, curs

    else:
        conn.close()
        return user


def send_reset_email(email, url):
    """Generates a confirmation code for a given account and sends a reset email.

    :param str email: the email linked to the account
    :param str url: the url of the running instance
    """
    user, conn, curs = confirmation(email, 'email', True)

    if user:

        validation_string = uuid.uuid4().hex
        stored_string = do_salt_hash(str(validation_string))

        confirm_link = (url + '/confirmuser?' +
                        urllib.urlencode({'code': str(validation_string)}))

        reset_link = (url + '/resetpassword?' +
                      urllib.urlencode({'code': str(validation_string)}))

        message_text = (
            'Hello ' + user +',\n\n'
            'A request to reset your password for this account has been submitted. '
            'If this request was created by you, please follow the following link: \n\n' +
            reset_link +
            '\n\nIf this request was not made by you, the previous link can be deactivated '
            'by folling the following: \n\n' +
            confirm_link +
            '\n\nand please report the incident to your local webmaster.'
            '\n\nThank you, \n'
            'Some machine'
            )

        send_email('daniel.abercrombie@cern.ch', email,
                   'Reset account on WorkflowWebTools Instance',
                   message_text)

        curs.execute('UPDATE users SET validator=?, isvalid=? WHERE username=?',
                     (stored_string, 0, user))
        conn.commit()

    conn.close()


def resetpassword(code, password):
    """Resets the password for a user.

    :param str code: is the validation code for the account
    :param str password: is the new password
    :returns: user from the password reset
    :rtype: str
    """

    user, conn, curs = confirmation(code, return_curs=True)

    if user:
        curs.execute('UPDATE users SET password=? WHERE username=?',
                     (do_salt_hash(password), user))
        conn.commit()

    conn.close()
    return user


def get_valid_emails():
    """Get iterator for valid email patterns for this instance.
    This is configurable by the webmaster.

    :returns: List of valid email patterns
    :rtype: list
    """

    emails = []

    with open('keys/valid_email.txt', 'r') as email_file:
        for valid_email in email_file.readlines():
            emails.append(valid_email.strip())

    return emails


def add_user(email, username, password, url):
    """Adds the user to the users database and sends a verification email,
       if the parameters are valid.

    .. todo::

      setup some webmaster configuration

    :param str email: The user email to send verification to.
                      Make sure to check for valid domains.
    :param str username: The username of the account to add
    :param str password: The password to be stored
    :param str url: The base url to redirect the user to for validating their account
    :returns: Success code. 0 for adding user, 1 for not adding
    :rtype: int
    """

    # Need to check parameters again so that some sneaky guy doesn't pass the javascript

    good_email = False

    for valid_email in get_valid_emails():
        if valid_email[0] == '@':
            if email.endswith(valid_email):
                good_email = True
                break

        elif email == valid_email:
            good_email = True
            break

    print good_email

    if not (good_email and re.match(r'^[A-za-z0-9]+$', username)) or password == '':
        return 1

    password = do_salt_hash(password)

    validation_string = uuid.uuid4().hex
    stored_string = do_salt_hash(str(validation_string))

    confirm_link = (url + '/confirmuser?' +
                    urllib.urlencode({'code': str(validation_string)}))

    message_text = (
        'Hello ' + username +',\n\n'
        'An account using this email has been registered on an instance of WorkflowWebTools. '
        'If this request was created by you, please follow the following link: \n\n' +
        confirm_link +
        '\n\nThank you, \n'
        'Some machine'
        )

    send_email('daniel.abercrombie@cern.ch', email,
               'Verify Account on WorkflowWebTools Instance',
               message_text)

    email = do_salt_hash(email)

    conn, curs = get_user_db()

    curs.execute('INSERT INTO users VALUES (?,?,?,?,?)',
                 (username, email, password, stored_string, 0))

    conn.commit()
    conn.close()

    return 0


def do_salt_hash(to_hash):
    """Salt and hash an object into a storable form.

    :param str to_hash: Alternate salt and hashing to get stored variable
    :returns: A salty hash
    :rtype: str
    """

    random.seed(to_hash)

    with open('keys/salt.txt', 'r') as salt_file:
        salts = [line.strip() for line in salt_file.readlines()]

    salt_len = len(salts)

    for _ in range(random.randint(10, 30)):

        to_hash = bcrypt.encrypt(to_hash, rounds=random.randint(5, 10),
                                 salt=salts[random.randint(0, 200) % salt_len])
        random.seed(to_hash)

    return to_hash
