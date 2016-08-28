"""
Tools for clustering workflows based on their errors

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import os
import numpy
import sklearn.cluster

from . import globalerrors


def get_workflow_vector(workflow, session=None):
    """
    Gets the errors for a workflow in a numpy array, vector form

    :param str workflow: is the workflow the vector is returned for
    :param cherrypy.Session session: Stores the information for a session
    :return: a 1-d vector of errors for the workflow
    :rtype: numpy.array
    """
    workflow_array = 0

    for step in globalerrors.get_step_list(workflow, session):
        step_array = []

        # Convert the 2-D table into a 1-D array
        for row in globalerrors.get_step_table(step, session):
            step_array += row

        # Add together the different steps in the workflow
        workflow_array += numpy.array(step_array)

    return workflow_array


def get_clusterer():
    """
    Use this function to get the clusterer of workflows

    :return: A clusterer that is fitted to historical data
    :rtype: sklearn.cluster
    """

    # This will be the location of our training data
    fake_session = {
        'info': globalerrors.ErrorInfo(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 
                'data', 'history.json'))
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

    return clusterer

