"""
Tools for clustering workflows based on their errors

:author: Daniel Abercrombie <dabercro@mit.edu>
"""


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

    if session:
        if session.get('wf_groups'):
            return session['wf_groups']

    workflows = globalerrors.check_session(session).return_workflows()
    vectors = []
    for workflow in workflows:
        vectors.append(
            get_workflow_vector(workflow, session, clusterer['allmap']))

    predictions = clusterer['clusterer'].predict(numpy.array(vectors))

    output = [set() for _ in range(clusterer['clusterer'].n_clusters)]
    for index, workflow in enumerate(workflows):
        output[predictions[index]].add(workflow)

    if session:
        session['wf_groups'] = output

    return output


def get_clustered_group(workflow, clusterer, session=None):
    """Get the group for a given workflow in this session

    :param str workflow: The workflow to get the group for.
    :param sklearn.cluster.KMeans clusterer: is the clusterer fit with
                                             historic data.
    :param cherrypy.Session session: Stores the information for a session
    :returns: List of other workflows in the same group
    :rtype: set
    """
    groups = get_workflow_groups(clusterer, session)

    output = set()

    for group in groups:
        if workflow in group:
            # Copy the existing set to the output variable
            output = set(group)

    output.discard(workflow)

    return output
