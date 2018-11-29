#pylint: disable=too-many-locals

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

import threading

import cherrypy
import numpy
import sklearn.cluster

from . import globalerrors
from . import serverconfig
from . import errorutils


def get_workflow_vectors(workflows, session=None, allmap=None):
    """
    Gets the errors for workflows in a list of numpy arrays

    :param str workflows: the workflows that vectors are returned for
    :param cherrypy.Session session: Stores the information for a session
    :param dict allmap: a globalerrors.ErrorInfo allmap to override the
                        session's allmap
    :return: a list of numpy arrays of errors for the workflow
    :rtype: list of numpy.array
    """
    curs = globalerrors.check_session(session, can_refresh=True)
    if not allmap:
        allmap = globalerrors.check_session(session).get_allmap()

    columns = ['errorcode', 'sitename']
    column_output = {}

    for column in columns:
        # Initialize with all zeros
        settings = serverconfig.config_dict()['cluster'][column]
        column_output[column] = [numpy.zeros(len(allmap[column])) for _ in workflows]

        cherrypy.log('Getting db_lock: 3')
        curs.db_lock.acquire()
        curs.curs.execute("SELECT SUM(numbererrors), {0}, stepname "
                          "FROM workflows "
                          "GROUP BY stepname, {0} "
                          "ORDER BY {0} ASC, stepname ASC;".format(column))

        numerrors, colval, stepname = curs.curs.fetchone() or (0, '', '')
        wfname = stepname.split('/')[1] if stepname else ''

        for icol, value in enumerate(allmap[column]):
            for iwkf, workflow in enumerate(workflows):
                while colval == value and workflow == wfname:
                    column_output[column][iwkf][icol] += numerrors
                    numerrors, colval, stepname = curs.curs.fetchone() or (0, '', '')
                    if stepname:
                        wfname = stepname.split('/')[1]

        cherrypy.log('releasing db_lock: 3')
        curs.db_lock.release()

        # Preprocessing here
        for output in column_output[column]:
            length = numpy.linalg.norm(output) or 1.0
            norm = (float(settings['distance'])/1.4142 +
                    2.0 * float(settings['width']) *
                    (length/(length + float(settings['midpoint'])) - 0.5))/length

            output *= float(norm)

    return [numpy.concatenate([column_output[col][iwkf] for col in columns]) \
                for iwkf, _ in enumerate(workflows)]


def get_clusterer(history_path, errors_path=''):
    """Use this function to get the clusterer of workflows

    :param str history_path: Path to the workflow historical data.
                             This can be a local file path or a URL.
    :param str errors_path: The errors for a given session to include
                            in the clustering
    :return: A dict of a clusterer that is fitted to historical data
             with its allmap. The keys are 'clusterer' and 'allmap'.
    :rtype: dict
    """

    cherrypy.log('Initializing cluster session')

    # This will be the location of our training data
    fake_session = {
        'info': globalerrors.ErrorInfo(history_path)
        }

    # If the path to additional errors is given, add that to the clustering data.
    if errors_path:
        errorutils.add_to_database(globalerrors.check_session(fake_session), errors_path)
        globalerrors.check_session(fake_session).set_all_lists()

    # Get the data by getting table for each workflow
    workflows = globalerrors.check_session(fake_session).return_workflows()

    # Fill the data
    cherrypy.log('Getting workflow vectors')
    data = get_workflow_vectors(workflows, fake_session)

    cherrypy.log('Number of datapoints to cluster: %i' % len(data))
    cherrypy.log('Fitting workflows...')

    settings = serverconfig.config_dict()['cluster']
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
    :returns: A dictionary pointing workflows to a group
    :rtype: dict
    """

    errorinfo = globalerrors.check_session(session, can_refresh=True)

    if errorinfo.clusters:
        return errorinfo.clusters

    cherrypy.log('Fitting existing workflows.')

    workflows = globalerrors.check_session(session).return_workflows()
    vectors = get_workflow_vectors(workflows, session, clusterer['allmap'])

    predictions = clusterer['clusterer'].predict(numpy.array(vectors))

    cherrypy.log(str(predictions))

    for index, workflow in enumerate(workflows):
        errorinfo.clusters[workflow] = predictions[index]

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

    output = []

    predictions = get_workflow_groups(clusterer, session)

    group = predictions.get(workflow)

    if group is not None:
        for wkf, cluster in predictions.iteritems():
            if cluster == group and wkf != workflow:
                output.append(wkf)

    return output


CLUSTER_LOCK = threading.Lock()
"""
Lock that should be acquired before running clustering functions in here
"""
