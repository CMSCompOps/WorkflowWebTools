"""
Tools for clustering workflows based on their errors.

The errors are clustered based on a generated vector.
The vector can be thought as lying on two different hyper-sphere shells.
One sphere is for the error codes that occur and
the other sphere is the sites where those errors occur.
The overall distance between two workflow will be the sum in quadrature
of the distances on these two hyper-spheres.

These distances are configurable in the server ``config.yml``.
Each sphere has a center radius, thickness, and number of errors to
be at the midpoint.
The equation to determine distance from the origin for a vector
of errors is the following.

.. math::

  \\mathrm{distance} = \\frac{d}{\\sqrt{2}} +
      2 w \\left(\\frac{|\\vec{v}|}{|\\vec{v}| + m} - 0.5\\right)

The following parameters are set in ``config.yml`` for the
site name and the error code hyperspheres separately.

- *m* is the 'midpoint' parameter is the number of errors at a given site
  or given error code that will place the workflow at the midpoint of the
  hypersphere shell.
- *d* is the 'distance' parameter is the cartesian distance between the midpoints
  of two different sites or error codes.
- *w* is the 'width' parameter which defines the total shell width that the workflow
  could possibly land on.

The direction is determined by the error code or site name distribution.
Note that this always points in the upper quadrant for a given coordinate.

The equation is chosen so that two workflows that have completely different
errors at the same site, and the error width is 0,
will end up with a distance that is equal to the error distance when clustering.
This way, site and errors can have different distance weights, and there
can be some separation for the number of errors in a workflow
(for non-zero width).

:author: Daniel Abercrombie <dabercro@mit.edu>
"""

import sqlite3

import cherrypy
import numpy
import sklearn.cluster

from . import globalerrors
from . import serverconfig


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
    workflow_array = []

    curs = globalerrors.check_session(session).curs
    if not allmap:
        allmap = globalerrors.check_session(session).get_allmap()

    cluster_settings = serverconfig.get_cluster_settings()

    def get_column_sum_list(column):
        """
        :param str column: is the column type to sum over
        :returns: a list of sums for each column in the column type
        :rtype: list
        """

        settings = cluster_settings[column]

        output = []
        for value in allmap[column]:
            curs.execute("SELECT COALESCE(SUM(numbererrors), 0) FROM workflows "
                         "WHERE stepname LIKE '/{0}/%' and {1}='{2}'".\
                             format(workflow, column, value))

            out = curs.fetchall()[0][0]
            output.append(float(out))

        if len(output) == 0:
            return output

        # Preprocessing here
        output = numpy.array(output)
        length = numpy.linalg.norm(output) or 1.0
        norm = (float(settings['distance'])/1.4142 +
                2.0 * float(settings['width']) *
                (length/(length + float(settings['midpoint'])) - 0.5))/length

        output *= float(norm)

        return list(output)

    workflow_array += get_column_sum_list('errorcode')
    workflow_array += get_column_sum_list('sitename')

    return numpy.array(workflow_array)


def get_clusterer(data_path):
    """Use this function to get the clusterer of workflows

    :param str data_path: Path to the workflow historical data.
                          This can be a local file path or a URL.
    :return: A dict of a clusterer that is fitted to historical data
             with its allmap. The keys are 'clusterer' and 'allmap'.
    :rtype: dict
    """

    cherrypy.log('Initializing cluster session')

    # This will be the location of our training data
    fake_session = {
        'info': globalerrors.ErrorInfo(data_path)
        }

    # Get the data by getting table for each workflow
    workflows = globalerrors.check_session(fake_session).return_workflows()

    # Fill the data
    data = []

    cherrypy.log('Getting workflow vectors')

    total = len(workflows)

    for iwf, workflow in enumerate(workflows):
        if iwf % 20 == 0:
            cherrypy.log(str(iwf) + '/' + str(total))

        workflow_array = get_workflow_vector(workflow, fake_session)

        # Bad training data returns empty list
        if len(workflow_array) != 0:
            data.append(workflow_array)

    cherrypy.log('Fitting workflows...')

    settings = serverconfig.get_cluster_settings()
    clusterer = sklearn.cluster.KMeans(n_clusters=settings['n_clusters'],
                                       n_init=settings['n_init'],
                                       n_jobs=-1)

    clusterer.fit(numpy.array(data))

    cherrypy.log('Done')

    return {'clusterer': clusterer, 'allmap': fake_session['info'].get_allmap()}


def get_workflow_groups(clusterer, session=None):
    """Groups workflows together based on a fitted clusterer

    :param dict clusterer: is a dictionary with the clusterer fit with
                           historic data and the allmap to generate it.
                           This matches the output of :func:`get_clusterer`.
    :param cherrypy.Session session: Stores the information for a session
    :returns: Lists of workflows grouped together
    :rtype: List of sets
    """

    errorinfo = globalerrors.check_session(session)

    if errorinfo.clusters:
        return errorinfo.clusters

    cherrypy.log('Fitting existing workflows.')

    workflows = globalerrors.check_session(session).return_workflows()
    vectors = []
    for workflow in workflows:
        vectors.append(
            get_workflow_vector(workflow, session, clusterer['allmap']))

    predictions = clusterer['clusterer'].predict(numpy.array(vectors))

    cherrypy.log(str(predictions))

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

    curs.execute('SELECT cluster, ROWID FROM groups WHERE workflow=?',
                 (workflow,))

    group = curs.fetchall()

    curs.execute('SELECT workflow FROM groups WHERE cluster=? AND ROWID!=?',
                 (group[0][0], group[0][1]))

    workflows = curs.fetchall()

    output = []
    for workflow in workflows:
        output.append(workflow[0])

    return output
