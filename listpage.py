"""
This module provides lists of workflows/site errors/sites, given the other two values

:author: Daniel Abercrombie
"""


from . import globalerrors


def i_matching_pievars(pievar, row, col, session=None):
    """
    Return an iterator of variables in pievar, and number of errors
    for a given rowname and colname

    :param str pievar: The variable to return an iterator of
    :param str row: Name of the row to match
    :param str col: Name of the column to match
    :param cherrypy.Session session: stores the session information
    """

    curs = globalerrors.check_session(session, True).curs
    rowname, colname = globalerrors.get_row_col_names(pievar)

    return list(curs.execute(('SELECT {0}, numbererrors FROM workflows '
                              'WHERE {1}=? AND {2}=?'.
                              format(pievar, rowname, colname)),
                             (row, col)))


def listworkflows(error_code, site_name, session=None):
    """
    Gives back a list of tuples containing workflows and the number of errors
    that matches a given error_code and site_name.

    :param int error_code: The error code that we want workflows for
    :param str site_name: The site name that we want workflows for
    :param cherrypy.Session session: holds the session information
    :returns: List of tuples of workflows and errors, sorted by number of errors
    :rtype: list
    """

    output_dict = {}

    for step, numerrors in i_matching_pievars('stepname', error_code, site_name, session):
        workflow = step.split('/')[1]
        output_dict[workflow] = output_dict.get(workflow, 0) + numerrors

    return sorted(output_dict.items(), key=lambda x: x[1], reverse=True)
