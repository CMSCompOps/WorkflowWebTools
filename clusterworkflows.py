"""
Tools for clustering workflows based on their errors

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import numpy
import sklearn.cluster

from . import globalerrors

def get_clusterer(session):
    """
    Use this function to get the clusterer of workflows

    :param cherrypy.Session session: Stores the information for a session
    :return: A clusterer that is fitted to data for the session.
    :rtype: sklearn.cluster
    """

    # Get the data by getting table for each workflow
    workflows = globalerrors.check_session(session).return_workflows()

    data = []

    for workflow in workflows:

        workflow_array = 0

        for step in globalerrors.get_step_list(workflow, session):
            step_array = []

            # Convert the 2-D table into a 1-D array
            for row in globalerrors.get_step_table(step, session):
                step_array += row

        # Add together the different steps in the workflow
        workflow_array += numpy.array(step_array)

        data.append(workflow_array)

    clusterer = sklearn.cluster.KMeans()
    clusterer.fit(numpy.array(data))

    return clusterer
