"""
Tools for clustering workflows based on their errors

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import sqlite3

import numpy
import sklearn.cluster

from . import globalerrors


def get_workflow_vector(workflow, session=None, allmap=None):
    """
    Gets the errors for a workflow in a numpy array, vector form

    :param str workflow: is the workflow the vector is returned for
    :param cherrypy.Session session: Stores the information for a session
    :param dict allmap: a globalerrors.ErrorInfo allmap to override the
                        session's allmap
    :return: a 1-d vector of errors for the workflow
    :rtype: numpy.array
    """
    workflow_array = 0

    for step in globalerrors.get_step_list(workflow, session):
        step_array = []

        # Convert the 2-D table into a 1-D array
        for row in globalerrors.get_step_table(step, session, allmap):
            step_array += row

        # Add together the different steps in the workflow
        workflow_array += numpy.array(step_array)

    return workflow_array


def get_clusterer(data_path):
    """Use this function to get the clusterer of workflows

    :param str data_path: Path to the workflow historical data.
                          This can be a local file path or a URL.
    :return: A dict of a clusterer that is fitted to historical data
             with its allmap
    :rtype: dict
    """

    # This will be the location of our training data
    fake_session = {
        'info': globalerrors.ErrorInfo(data_path)
        }

    # Get the data by getting table for each workflow
    workflows = globalerrors.check_session(fake_session).return_workflows()

    # Fill the data
    data = []

    for workflow in workflows:
        workflow_array = get_workflow_vector(workflow, fake_session)

        # Bad training data returns int(0)
        if not isinstance(workflow_array, int):
            data.append(workflow_array)

    clusterer = sklearn.cluster.KMeans()

    clusterer.fit(numpy.array(data))

    return {'clusterer': clusterer, 'allmap': fake_session['info'].get_allmap()}


def get_workflow_groups(clusterer, session=None):
    """Groups workflows together based on a fitted clusterer

    :param sklearn.cluster.KMeans clusterer: is the clusterer fit with
                                             historic data.
    :param cherrypy.Session session: Stores the information for a session
    :returns: Lists of workflows grouped together
    :rtype: List of sets
    """

    errorinfo = globalerrors.check_session(session)

    if errorinfo.clusters:
        return errorinfo.clusters

    workflows = globalerrors.check_session(session).return_workflows()
    vectors = []
    for workflow in workflows:
        vectors.append(
            get_workflow_vector(workflow, session, clusterer['allmap']))

    predictions = clusterer['clusterer'].predict(numpy.array(vectors))

    conn = sqlite3.connect(':memory:', check_same_thread=False)
    curs = conn.cursor()

    curs.execute(
        'CREATE TABLE groups (workflow varchar(255), cluster int)')

    for index, workflow in enumerate(workflows):
        curs.execute('INSERT INTO groups VALUES (\'{0}\',{1})'.\
                         format(workflow, predictions[index]))

    errorinfo.clusters = {
        'conn': conn,
        'curs': curs
        }

    return errorinfo.clusters


def get_clustered_group(workflow, clusterer, session=None):
    """Get the group for a given workflow in this session

    :param str workflow: The workflow to get the group for.
    :param sklearn.cluster.KMeans clusterer: is the clusterer fit with
                                             historic data.
    :param cherrypy.Session session: Stores the information for a session
    :returns: List of other workflows in the same group
    :rtype: set
    """
    curs = get_workflow_groups(clusterer, session)['curs']

    curs.execute('SELECT cluster FROM groups WHERE workflow=?',
                 (workflow,))

    group = curs.fetchall()

    curs.execute('SELECT workflow FROM groups WHERE workflow!=? AND cluster=?',
                 (workflow, group[0][0]))

    workflows = curs.fetchall()

    output = []
    for workflow in workflows:
        output.append(workflow[0])

    return output
